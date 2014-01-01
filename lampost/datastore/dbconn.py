from redis import ConnectionPool
from redis.client import StrictRedis
from lampost.datastore.exceptions import ObjectExistsError, NonUniqueError

from lampost.util.lmlog import logged
from lampost.context.resource import requires, provides, m_requires

m_requires('log', 'json_encode', 'json_decode', 'cls_registry', __name__)


@provides('datastore', export_methods=True)
class RedisStore():
    def __init__(self, db_host, db_port, db_num, db_pw):
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw)
        self.redis = StrictRedis(connection_pool=pool)
        self._object_map = {}

    def create_object(self, base_class, dbo_dict):
        dbo_class = cls_registry(dbo_dict.get('class_id', base_class))
        dbo_id = dbo_dict['dbo_id']
        if self.object_exists(dbo_class.dbo_key_type, dbo_id):
            raise ObjectExistsError(dbo_id)
        dbo = dbo_class(dbo_id)
        self._hydrate_dbo(dbo, dbo_dict)
        dbo.on_created()
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, dbo.dbo_id)
        self.save_object(dbo, True)
        dbo.on_loaded()
        return dbo

    def save_object(self, dbo, update_rev=False, autosave=False):
        if update_rev:
            rev = getattr(dbo, "dbo_rev", None)
            dbo.dbo_rev = 1 if not rev else rev + 1
        if dbo.dbo_indexes:
            self.update_indexes(dbo)
        self.redis.set(dbo.dbo_key, json_encode(dbo.save_dbo_dict))
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
        return self._object_map.get(unicode('{0}:{1}'.format(key_type, key)))

    def evict_object(self, dbo):
        if not self._object_map.pop(dbo.dbo_key):
            warn("Failed to evict " + dbo.dbo_key + " from db cache", self)

    @logged
    def load_by_key(self, key_type, key, base_class=None):
        dbo_key = unicode('{0}:{1}'.format(key_type, key))
        cached_dbo = self._object_map.get(dbo_key)
        if cached_dbo:
            return cached_dbo
        json_str = self.redis.get(dbo_key)
        if not json_str:
            return None
        dbo_dict = json_decode(json_str)
        dbo = cls_registry(dbo_dict.get('class_id', base_class))(key)
        self._object_map[dbo.dbo_key] = dbo
        self._hydrate_dbo(dbo, dbo_dict)
        dbo.on_loaded()
        return dbo

    def object_exists(self, obj_type, obj_id):
        return self.redis.exists(unicode('{}:{}'.format(obj_type, obj_id)))

    def load_object(self, dbo_class, key):
        return self.load_by_key(dbo_class.dbo_key_type, key, dbo_class)

    def load_object_set(self, dbo_class, set_key=None):
        if not set_key:
            set_key = dbo_class.dbo_set_key
        return [self.load_object(dbo_class, dbo_id) for dbo_id in self.fetch_set_keys(set_key)]

    def delete_object_set(self, dbo_class, set_key=None):
        if not set_key:
            set_key = dbo_class.dbo_set_key
        for dbo in self.load_object_set(dbo_class, set_key):
            self.delete_object(dbo)
        self.delete_key(set_key)

    def update_object(self, dbo, dbo_dict):
        self._hydrate_dbo(dbo, dbo_dict)
        self.save_object(dbo, True)

    def delete_object(self, dbo):
        key = dbo.dbo_key
        self.redis.delete(key)
        if dbo.dbo_set_key:
            self.redis.srem(dbo.dbo_set_key, dbo.dbo_id)
        for ix_name in dbo.dbo_indexes:
            ix_value = getattr(dbo, ix_name, None)
            if ix_value is not None and ix_value != '':
                self.delete_index('ix:{}:{}'.format(dbo.dbo_key_type, ix_name), ix_value)
        if __debug__:
            debug("object deleted: {}".format(key), self)
        try:
            self._object_map.pop(dbo.dbo_key)
        except KeyError:
            warn("Removing object {} not previously cached".format(dbo.dbo_id))

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

    def get_all_index(self, index_name):
        return self.redis.hgetall(index_name)

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

    def update_indexes(self, dbo):
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

    def _hydrate_dbo(self, dbo, dbo_dict):
        dbo.hydrate(dbo_dict)
        return

        for field_name in dbo.dbo_fields:
            try:
                setattr(dbo, field_name, dbo_dict[field_name])
            except KeyError:
                dbo.__dict__.pop(field_name, None)

        for dbo_map in dbo.dbo_maps:
            raw_list = dbo_dict.get(dbo_map.field_name, None)
            if raw_list:
                coll = dbo_map.instance(dbo)
                for child_dbo_id, child_json in raw_list.iteritems():
                    child_template = self.load_object(dbo_map.base_class, child_dbo_id)
                    if child_template:
                        child_dbo = child_template.create_instance(dbo)
                        self._hydrate_dbo(child_dbo, child_json)
                        coll[child_dbo_id] = child_dbo
                    else:
                        warn("Missing template for {}".format(child_dbo_id))
            else:
                dbo.__dict__.pop(dbo_map.field_name, None)
