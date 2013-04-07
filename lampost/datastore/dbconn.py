from redis import ConnectionPool
from redis.client import StrictRedis
from lampost.datastore.exceptions import ObjectExistsError, NonUniqueError

from lampost.util.lmlog import logged
from lampost.context.resource import requires, provides, m_requires

m_requires('log', __name__)


@provides('datastore', True)
@requires('json_decode', 'json_encode', 'cls_registry')
class RedisStore():
    def __init__(self, db_host, db_port, db_num, db_pw):
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw)
        self.redis = StrictRedis(connection_pool=pool)
        self._class_map = {}
        self._object_map = {}

    def create_object(self, dbo):
        if self.object_exists(dbo.dbo_key_type, dbo.dbo_id):
            raise ObjectExistsError(dbo.dbo_key)
        save_object(dbo)
        dbo.on_loaded()

    def save_object(self, dbo, update_rev=False, autosave=False):
        if update_rev:
            rev = getattr(dbo, "dbo_rev", None)
            dbo.dbo_rev = 1 if not rev else rev + 1
        if dbo.dbo_indexes:
            self.update_indexes(dbo)
        self.redis.set(dbo.dbo_key, self.json_encode(dbo.save_dbo_dict))
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, dbo.dbo_key)
        trace("db object {} {}saved".format(dbo.dbo_key, "auto" if autosave else ""), self)
        self._object_map[dbo.dbo_key] = dbo

    def load_cached(self, key):
        return self._object_map.get(key)

    def evict_object(self, dbo):
        try:
            del self._object_map[dbo.dbo_key]
            del dbo
        except KeyError:
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
        dbo_dict = self.json_decode(json_str)
        dbo = self._load_class(dbo_dict, base_class)(key)
        if dbo.dbo_key_type:
            self._object_map[dbo.dbo_key] = dbo
        self.hydrate_dbo(dbo, dbo_dict)
        return dbo

    def object_exists(self, obj_type, obj_id):
        return self.redis.exists(unicode('{}:{}'.format(obj_type, obj_id)))

    def load_object(self, dbo_class, key):
        return self.load_by_key(dbo_class.dbo_key_type, key, dbo_class)

    def update_object(self, dbo, dbo_dict):
        self.hydrate_dbo(dbo, dbo_dict)
        self.save_object(dbo, True)

    def delete_object(self, dbo):
        key = dbo.dbo_key
        self.redis.delete(key)
        if dbo.dbo_set_key:
            self.redis.srem(dbo.dbo_set_key, key)
        for dbo_col in dbo.dbo_collections:
            if dbo_col.key_type:
                coll = getattr(dbo, dbo_col.field_name, set())
                for child_dbo in coll:
                    self.delete_object(child_dbo)
        for ix_name in dbo.dbo_indexes:
            ix_value = getattr(dbo, ix_name, None)
            if ix_value is not None and ix_value != '':
                self.delete_index('ix:{}:{}'.format(dbo.dbo_key_type, ix_name), ix_value)
        debug("object deleted: " + key, self)
        if self._object_map.get(dbo.dbo_key):
            del self._object_map[dbo.dbo_key]
        return True

    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)

    def add_set_key(self, set_key, value):
        self.redis.sadd(set_key, value)

    def delete_set_key(self, set_key, value):
        self.redis.srem(set_key, value)

    def set_key_exists(self, set_key, value):
        return self.redis.sismember(set_key, value)

    def delete_key(self, key):
        self.redis.delete(key)

    def set_index(self, index_name, key, value):
        return self.redis.hset(index_name, key, value)

    def get_index(self, index_name, key):
        return self.redis.hget(index_name, key)

    def delete_index(self, index_name, key):
        return self.redis.hdel(index_name, key)

    def update_indexes(self, dbo):
        try:
            old_dbo = self.json_decode(self.redis.get(dbo.dbo_key))
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
                self.set_index(ix_key, new_val, dbo.dbo_key)

    def build_indexes(self, dbo_cls):
        for ix_name in dbo_cls.dbo_indexes:
            self.redis.delete('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name))
        for dbo_id in self.fetch_set_keys(dbo_cls.dbo_set_key):
            try:
                dbo_dict = self.json_decode(self.redis.get(dbo_id))
                for ix_name in dbo_cls.dbo_indexes:
                    ix_value = dbo_dict.get(ix_name)
                    if ix_value is not None and ix_value != '':
                        self.set_index('ix:{}:{}'.format(dbo_cls.dbo_key_type, ix_name), ix_value, dbo_id)
            except (ValueError, TypeError):
                warn("Missing dbo object {} from set key {}".format(dbo_id, dbo_cls.dbo_set_key, self))

    def hydrate_dbo(self, dbo, dbo_dict):
        for field_name in dbo.dbo_fields:
            try:
                setattr(dbo, field_name, dbo_dict[field_name])
            except KeyError:
                pass
        for dbo_col in dbo.dbo_collections:
            coll = getattr(dbo, dbo_col.field_name, [])
            try:
                for child_json in dbo_dict[dbo_col.field_name]:
                    try:
                        if dbo_col.key_type:
                            child_dbo = self.load_by_key(dbo_col.key_type, child_json, dbo_col.base_class)
                        else:
                            child_dbo = self._load_class(child_json, dbo_col.base_class)()
                            self.hydrate_dbo(child_dbo, child_json)
                        coll.append(child_dbo)
                    except AttributeError:
                        warn("{} json failed to load for coll {} in {}".format(child_json, dbo_col.field_name, unicode(dbo.dbo_id)), self)
            except KeyError:
                if dbo.dbo_key_type:
                    trace("db: Object " + unicode(dbo.dbo_debug_key) + " json missing collection " + dbo_col.field_name, self)

        for dbo_ref in dbo.dbo_refs:
            try:
                ref_key = dbo_dict[dbo_ref.field_name]
                ref_obj = self.load_by_key(dbo_ref.key_type, ref_key, dbo_ref.base_class)
                setattr(dbo, dbo_ref.field_name, ref_obj)
            except KeyError:
                if dbo.dbo_key_type:
                    trace("db: Object " + unicode(dbo.dbo_debug_key) + " json missing ref " + dbo_ref.field_name, self)
        dbo.on_loaded()
        return True

    def _load_class(self, dbo_dict, base_class):
        class_path = dbo_dict.get("class_name")
        if not class_path:
            return self.cls_registry(base_class)
        cls = self._class_map.get(class_path)
        if cls:
            return cls
        split_path = class_path.split(".")
        module_name = ".".join(split_path[:-1])
        class_name = split_path[-1]
        module = __import__(module_name, globals(), locals(), [class_name])
        cls = getattr(module, class_name)
        cls = self.cls_registry(cls)
        self._class_map[class_path] = cls
        return cls

