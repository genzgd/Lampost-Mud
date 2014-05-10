from collections import defaultdict
from weakref import WeakValueDictionary
from redis import ConnectionPool
from redis.client import StrictRedis
from lampost.datastore.classes import get_dbo_class
from lampost.datastore.exceptions import ObjectExistsError, NonUniqueError

from lampost.util.lmlog import logged
from lampost.context.resource import provides, m_requires

m_requires('log', 'json_encode', 'json_decode', __name__)


class RedisStore():
    def __init__(self, db_host, db_port, db_num, db_pw):
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw)
        self.redis = StrictRedis(connection_pool=pool)
        self._object_map = WeakValueDictionary()

    def create_object(self, dbo_class, dbo_dict):
        dbo_class = get_dbo_class(dbo_dict.get('sub_class_id', dbo_class.dbo_key_type))
        dbo_id = dbo_dict['dbo_id']
        if self.object_exists(dbo_class.dbo_key_type, dbo_id):
            raise ObjectExistsError(dbo_id)
        dbo = dbo_class(dbo_id)
        dbo.hydrate(dbo_dict)
        dbo.on_created()
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, dbo.dbo_id)
        self.save_object(dbo, True)
        return dbo

    def save_object(self, dbo, update_rev=False, autosave=False):
        if update_rev:
            rev = getattr(dbo, "dbo_rev", None)
            dbo.dbo_rev = 1 if not rev else rev + 1
        if dbo.dbo_indexes:
            self._update_indexes(dbo)
        self.redis.set(dbo.dbo_key, json_encode(self._save_root(dbo)))
        if __debug__:
            debug("db object {} {}saved".format(dbo.dbo_key, "auto" if autosave else ""), self)
        self._object_map[dbo.dbo_key] = dbo

    def save_raw(self, key, raw):
        self.redis.set(key, json_encode(raw))

    def load_raw(self, key, default=None):
        json = self.redis.get(key)
        if json:
            return json_decode(json)
        return default

    def load_cached(self, key_type, key):
        return self._object_map.get(unicode('{}:{}'.format(key_type, key)))

    @logged
    def load_by_key(self, key_type, key, silent=False):
        dbo_key = unicode('{}:{}'.format(key_type, key))
        cached_dbo = self._object_map.get(dbo_key)
        if cached_dbo:
            return cached_dbo
        json_str = self.redis.get(dbo_key)
        if not json_str:
            if not silent:
                warn("Failed to find {} in database".format(dbo_key))
            return None
        dbo_dict = json_decode(json_str)
        dbo_cls = get_dbo_class(dbo_dict.get('sub_class_id', key_type))
        dbo = dbo_cls(key)
        self._object_map[dbo.dbo_key] = dbo
        dbo.hydrate(dbo_dict)
        return dbo

    def object_exists(self, obj_type, obj_id):
        return self.redis.exists(unicode('{}:{}'.format(obj_type, obj_id)))

    def load_object(self, dbo_class, key):
        return self.load_by_key(dbo_class.dbo_key_type, key)

    def load_object_set(self, dbo_class, set_key=None):
        if not set_key:
            set_key = dbo_class.dbo_set_key
        results = []
        for dbo_id in self.fetch_set_keys(set_key):
            obj = self.load_object(dbo_class, dbo_id)
            if obj:
                results.append(obj)
            else:
                warn("Removing missing object from set {}".format(set_key))
                self.delete_set_key(set_key, dbo_id)
        return results

    def delete_object_set(self, dbo_class, set_key=None):
        if not set_key:
            set_key = dbo_class.dbo_set_key
        for dbo in self.load_object_set(dbo_class, set_key):
            self.delete_object(dbo)
        self.delete_key(set_key)

    def update_object(self, dbo, dbo_dict):
        dbo.hydrate(dbo_dict)
        self.save_object(dbo, True)

    def delete_object(self, dbo):
        key = dbo.dbo_key
        self.redis.delete(key)
        self._clear_old_refs(dbo)
        if dbo.dbo_set_key:
            self.redis.srem(dbo.dbo_set_key, dbo.dbo_id)
        for children_type in dbo.dbo_children_types:
            self.delete_object_set(get_dbo_class(children_type), "{}_{}s:{}".format(dbo.dbo_key_type, children_type, dbo.dbo_id))
        for ix_name in dbo.dbo_indexes:
            ix_value = getattr(dbo, ix_name, None)
            if ix_value is not None and ix_value != '':
                self.delete_index('ix:{}:{}'.format(dbo.dbo_key_type, ix_name), ix_value)
        if __debug__:
            debug("object deleted: {}".format(key), self)
        self.evict_object(dbo)

    def reload_object(self, key_type, key):
        dbo = self.load_cached(key_type, key)
        if not dbo:
            return load_by_key(key_type, key)
        json_str = self.redis.get(unicode('{}:{}'.format(key_type, key)))
        if not json_str:
            warn("Failed to find {} in database for reload".format(dbo_key))
            return None
        self.update_object(dbo, json_decode(json_str))
        return dbo

    def evict_object(self, dbo):
        self._object_map.pop(dbo.dbo_key, None)

    def fetch_holders(self, key_type, dbo_id):
        holder_keys = []
        for holder_key in self.fetch_set_keys(self._holder_key(key_type, dbo_id)):
            key_split = holder_key.split(':')
            holder_keys.append((key_split[0], ':'.join(key_split[1:])))
        return holder_keys

    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)

    def add_set_key(self, set_key, value):
        self.redis.sadd(set_key, value)

    def delete_set_key(self, set_key, value):
        self.redis.srem(set_key, value)

    def set_key_exists(self, set_key, value):
        return self.redis.sismember(set_key, value)

    def db_counter(self, counter_id, inc=1):
        return self.redis.incr("counter:{}".format(counter_id), inc)

    def delete_key(self, key):
        self.redis.delete(key)

    def set_index(self, index_name, key, value):
        return self.redis.hset(index_name, key, value)

    def get_index(self, index_name, key):
        return self.redis.hget(index_name, key)

    def delete_index(self, index_name, key):
        return self.redis.hdel(index_name, key)

    def get_all_hash(self, index_name):
        return {key: json_decode(value) for key, value in self.redis.hgetall(index_name).viewitems()}

    def set_db_hash(self, hash_id, hash_key, value):
        return self.redis.hset(hash_id, hash_key, json_encode(value))

    def get_db_hash(self, hash_id, hash_key):
        return json_decode(self.redis.hget(hash_id, hash_key))

    def remove_db_hash(self, hash_id, hash_key):
        self.redis.hdel(hash_id, hash_key)

    def get_all_db_hash(self, hash_id):
        return [json_decode(value) for value in self.redis.hgetall(hash_id).itervalues()]

    def get_db_list(self, list_id, start=0, end=-1):
        return [json_decode(value) for value in self.redis.lrange(list_id, start, end)]

    def add_db_list(self, list_id, value):
        self.redis.lpush(list_id, json_encode(value))

    def trim_db_list(self, list_id, start, end):
        return self.redis.ltrim(list_id, start, end)

    def _update_indexes(self, dbo):
        try:
            old_dbo = json_decode(self.redis.get(dbo.dbo_key))
        except TypeError:
            old_dbo = None

        for ix_name in dbo.dbo_indexes:
            new_val = getattr(dbo, ix_name, None)
            old_val = old_dbo.get(ix_name) if old_dbo else None
            if old_val == new_val:
                continue
            ix_key = 'ix:{}:{}'.format(dbo.dbo_key_type, ix_name)
            if old_val is not None:
                self.delete_index(ix_key, old_val)
            if new_val is not None and new_val != '':
                if self.get_index(ix_key, new_val):
                    raise NonUniqueError(ix_key, new_val)
                self.set_index(ix_key, new_val, dbo.dbo_id)

    def _save_root(self, root_dbo):
        self._clear_old_refs(root_dbo)
        new_refs = defaultdict(list)

        def add_refs(dbo):
            if dbo.dbo_key_type and root_dbo != dbo:
                for attr in ['dbo_id', 'template_id']:
                    dbo_id = getattr(dbo, attr, None)
                    if dbo_id:
                        new_refs[dbo.dbo_key_type].append(dbo_id)

        def save_level(dbo, first=False):
            add_refs(dbo)
            if getattr(dbo, 'dbo_id', None) and not first:
                return dbo.dbo_id
            save_value = {}
            for field, dbo_field in dbo.dbo_fields.viewitems():
                try:
                    field_value = dbo.__dict__[field]
                except KeyError:
                    continue
                if hasattr(dbo_field, 'dbo_class_id'):
                    field_value = dbo_field.value_wrapper(save_level)(field_value)
                try:
                    dbo_field.should_save(field_value, dbo)
                except KeyError:
                    continue
                save_value[field] = field_value
            return dbo.metafields(save_value, ['sub_class_id', 'template_id'])

        root_save = save_level(root_dbo, True)
        self._set_new_refs(root_dbo, new_refs)
        return root_save

    def _clear_old_refs(self, dbo):
        dbo_key = dbo.dbo_key
        ref_key = unicode("{}:refs".format(dbo_key))
        for key_type, refs in self.get_all_hash(ref_key).viewitems():
            for ref_id in refs:
                self.delete_set_key(self._holder_key(key_type, ref_id), dbo_key)
        self.delete_key(ref_key)

    def _set_new_refs(self, dbo, new_refs):
        dbo_key = dbo.dbo_key
        ref_key = unicode("{}:refs".format(dbo_key))
        for key_type, refs in new_refs.viewitems():
            self.set_db_hash(ref_key, key_type, refs)
            for ref_id in refs:
                self.add_set_key(self._holder_key(key_type, ref_id), dbo_key)

    def _holder_key(self, key_type, dbo_id):
        return unicode("{}:{}:hldrs".format(key_type, dbo_id))
