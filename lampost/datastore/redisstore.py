from collections import defaultdict, deque
from weakref import WeakValueDictionary
from redis import ConnectionPool
from redis.client import StrictRedis
from lampost.datastore.classes import get_dbo_class, get_mixed_type
from lampost.datastore.dbo import Untyped
from lampost.datastore.exceptions import ObjectExistsError, NonUniqueError

from lampost.util.log import logged
from lampost.context.resource import m_requires

m_requires(__name__, 'log', 'json_encode', 'json_decode')


class RedisStore():
    def __init__(self, db_host, db_port, db_num, db_pw):
        self.pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw,
                                   decode_responses=True)
        self.redis = StrictRedis(connection_pool=self.pool)
        self._object_map = WeakValueDictionary()

    def create_object(self, dbo_class, dbo_dict):
        dbo_class = get_dbo_class(dbo_class.dbo_key_type)
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
        debug("db object {} {}saved", dbo.dbo_key, "auto" if autosave else "")
        self._object_map[dbo.dbo_key] = dbo
        return dbo

    def save_raw(self, key, raw):
        self.redis.set(key, json_encode(raw))

    def load_raw(self, key, default=None):
        json = self.redis.get(key)
        if json:
            return json_decode(json)
        return default

    def load_cached(self, dbo_key):
        return self._object_map.get(dbo_key)

    @logged
    def load_object(self, dbo_class, dbo_id, silent=False):
        dbo_key, dbo_id, class_id = dbo_class.dbo_defs(dbo_id)
        cached_dbo = self._object_map.get(dbo_key)
        if cached_dbo:
            return cached_dbo
        json_str = self.redis.get(dbo_key)
        if not json_str:
            if not silent:
                warn("Failed to find {} in database", dbo_key)
            return None
        return self.load_from_json(json_str, class_id, dbo_id)

    def load_from_json(self, json_str, class_id, dbo_id):
        dbo_dict = json_decode(json_str)
        dbo = get_mixed_type(class_id, dbo_dict.get('mixins'))(dbo_id)
        self._object_map[dbo.dbo_key] = dbo
        dbo.hydrate(dbo_dict)
        return dbo

    def object_exists(self, obj_type, obj_id):
        return self.redis.exists('{}:{}'.format(obj_type, obj_id))

    def load_object_set(self, dbo_class, set_key=None):
        key_type = dbo_class.dbo_key_type
        if not set_key:
            set_key = dbo_class.dbo_set_key
        results = set()
        keys = deque()
        pipeline = self.redis.pipeline()
        for key in self.fetch_set_keys(set_key):
            dbo_key = ':'.join([key_type, key])
            try:
                results.add(self._object_map[dbo_key])
            except KeyError:
                keys.append(key)
                pipeline.get(dbo_key)
        for dbo_id, json_str in zip(keys, pipeline.execute()):
            if json_str:
                obj = self.load_from_json(json_str, key_type, dbo_id)
                if obj:
                    results.add(obj)
                continue
            warn("Removing missing object from set {}", set_key)
            self.delete_set_key(set_key, key)
        return results

    def delete_object_set(self, dbo_class, set_key=None):
        if not set_key:
            set_key = dbo_class.dbo_set_key
        for dbo in self.load_object_set(dbo_class, set_key):
            self.delete_object(dbo)
        self.delete_key(set_key)

    def update_object(self, dbo, dbo_dict):
        dbo.hydrate(dbo_dict)
        return self.save_object(dbo, True)

    def delete_object(self, dbo):
        key = dbo.dbo_key
        dbo.on_deleted()
        self.redis.delete(key)
        self._clear_old_refs(dbo)
        if dbo.dbo_set_key:
            self.redis.srem(dbo.dbo_set_key, dbo.dbo_id)
        for children_type in dbo.dbo_children_types:
            self.delete_object_set(get_dbo_class(children_type),
                                   "{}_{}s:{}".format(dbo.dbo_key_type, children_type, dbo.dbo_id))
        for ix_name in dbo.dbo_indexes:
            ix_value = getattr(dbo, ix_name, None)
            if ix_value is not None and ix_value != '':
                self.delete_index('ix:{}:{}'.format(dbo.dbo_key_type, ix_name), ix_value)
        debug("object deleted: {}", key)
        self.evict_object(dbo)

    def reload_object(self, dbo_key):
        dbo = self._object_map.get(dbo_key)
        if dbo:
            json_str = self.redis.get(dbo_key)
            if not json_str:
                warn("Failed to find {} in database for reload", dbo_key)
                return None
            return self.update_object(dbo, json_decode(json_str))
        return self.load_object(Untyped, dbo_key)

    def evict_object(self, dbo):
        self._object_map.pop(dbo.dbo_key, None)

    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)

    def add_set_key(self, set_key, *values):
        self.redis.sadd(set_key, *values)

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

    def get_full_index(self, index_name):
        return self.redis.hgetall(index_name)

    def delete_index(self, index_name, key):
        return self.redis.hdel(index_name, key)

    def get_all_hash(self, index_name):
        return {key: json_decode(value) for key, value in self.redis.hgetall(index_name).items()}

    def set_db_hash(self, hash_id, hash_key, value):
        return self.redis.hset(hash_id, hash_key, json_encode(value))

    def get_db_hash(self, hash_id, hash_key):
        return json_decode(self.redis.hget(hash_id, hash_key))

    def remove_db_hash(self, hash_id, hash_key):
        self.redis.hdel(hash_id, hash_key)

    def get_all_db_hash(self, hash_id):
        return [json_decode(value) for value in self.redis.hgetall(hash_id).values()]

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
        new_refs = []

        def add_refs(dbo):
            if dbo.dbo_key_type and root_dbo != dbo:
                if hasattr(dbo, 'dbo_id'):
                    new_refs.append(dbo.dbo_key)
                elif getattr(dbo, 'template_key', None):
                    new_refs.append(dbo.template_key)

        def child_dbo(dbo, dbo_field_class):
            class_id = getattr(dbo, 'class_id', dbo_field_class)
            save_value = save_level(dbo, get_dbo_class(class_id).dbo_key_type)
            if hasattr(dbo, 'template_key'):
                save_value['template_key'] = dbo.template_key
            elif class_id != dbo_field_class:
                # If the object has a different class_id than field definition thinks it should have
                # we need to save the actual class_id
                save_value['class_id'] = class_id
            return save_value

        def save_level(dbo, save_as_ref=False):
            add_refs(dbo)
            if save_as_ref:
                return dbo.dbo_id
            save_value = {}
            for field, dbo_field in dbo.dbo_fields.items():
                try:
                    field_value = dbo.__dict__[field]
                except KeyError:
                    continue

                dbo_field_class = getattr(dbo_field, 'dbo_class_id', None)
                if dbo_field_class:
                    field_value = dbo_field.value_wrapper(child_dbo)(field_value, dbo_field_class)
                try:
                    dbo_field.should_save(field_value, dbo)
                except KeyError:
                    continue
                save_value[field] = field_value
            return save_value

        root_save = save_level(root_dbo)
        if new_refs:
            self._set_new_refs(root_dbo, new_refs)
        return root_save

    def _clear_old_refs(self, dbo):
        dbo_key = dbo.dbo_key
        ref_key = '{}:refs'.format(dbo_key)
        for ref_id in self.fetch_set_keys(ref_key):
            holder_key = '{}:holders'.format(ref_id)
            self.delete_set_key(holder_key, dbo_key)
        self.delete_key(ref_key)

    def _set_new_refs(self, dbo, new_refs):
        dbo_key = dbo.dbo_key
        self.add_set_key("{}:refs".format(dbo_key), new_refs)
        for ref_id in new_refs:
            holder_key = '{}:holders'.format(ref_id)
            self.add_set_key(holder_key, dbo_key)
