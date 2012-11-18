from redis import ConnectionPool
from redis.client import StrictRedis

from lampost.util.lmlog import logged
from lampost.context.resource import requires, provides, m_requires

m_requires('log', __name__)

@provides('datastore', True)
@requires('dispatcher', 'decode', 'encode', 'cls_registry')
class RedisStore():
    def __init__(self, db_host, db_port, db_num, db_pw):
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw)
        self.redis = StrictRedis(connection_pool=pool)
        self.class_map = {}
        self.object_map = {}

    def create_object(self, dbo, update_rev=False):
        self.save_object(dbo, update_rev)
        dbo.on_loaded()

    def save_object(self, dbo, update_rev=False, autosave=False):
        if update_rev:
            rev = getattr(dbo, "dbo_rev", None)
            dbo.dbo_rev = 1 if not rev else rev + 1
        dbo.before_save()
        key = dbo.dbo_key
        self.redis.set(key, self.encode(dbo.save_json_obj))
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, key)
        self.dispatch("db_log{0}".format("_auto" if autosave else ""), "object saved: " + key)
        self.object_map[dbo.dbo_key] = dbo

    def load_cached(self, key):
        return self.object_map.get(key)

    def evict_object(self, dbo):
        try:
            del self.object_map[dbo.dbo_key]
        except:
            db_log("Failed to evict " + dbo.dbo_key + " from db cache")

    @logged
    def load_by_key(self, key_type, key, base_class=None):
        dbo_key = unicode('{0}:{1}'.format(key_type, key))
        cached_dbo = self.object_map.get(dbo_key)
        if cached_dbo:
            return cached_dbo
        json_str = self.redis.get(dbo_key)
        if not json_str:
            return None
        json_obj = self.decode(json_str)
        dbo = self._load_class(json_obj, base_class)(key)
        if dbo.dbo_key_type:
            self.object_map[dbo.dbo_key] = dbo
        self.load_json(dbo, json_obj)
        return dbo

    def object_exists(self, type, id):
        key = '{0}:{1}'.format(type, id)
        return self.redis.keys(key) == key

    def load_object(self, dbo_class, key):
        return self.load_by_key(dbo_class.dbo_key_type, key, dbo_class)

    def update_object(self, dbo, json_obj):
        self.load_json(dbo, json_obj)
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
        db_log("object deleted: " + key)
        if self.object_map.get(dbo.dbo_key):
            del self.object_map[dbo.dbo_key]
        return True

    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)

    def set_index(self, index_name, key, value):
        return self.redis.hset(index_name, key, value)

    def get_index(self, index_name, key):
        return self.redis.hget(index_name, key)

    def delete_index(self, index_name, key):
        return self.redis.hdel(index_name, key)

    def _load_class(self, json_obj, base_class):
        class_path = json_obj.get("class_name")
        if not class_path:
            return self.cls_registry(base_class)
        clazz = self.class_map.get(class_path)
        if clazz:
            return clazz
        split_path = class_path.split(".")
        module_name = ".".join(split_path[:-1])
        class_name = split_path[-1]
        module = __import__(module_name, globals(), locals(), [class_name])
        clazz = getattr(module, class_name)
        clazz = self.cls_registry(clazz)
        self.class_map[class_path] = clazz
        return clazz

    def load_json(self, dbo, json_obj):
        for field_name in dbo.dbo_fields:
            try:
                setattr(dbo, field_name, json_obj[field_name])
            except KeyError:
                pass
        for dbo_col in dbo.dbo_collections:
            coll = getattr(dbo, dbo_col.field_name, [])
            try:
                for child_json in json_obj[dbo_col.field_name]:
                    try:
                        if dbo_col.key_type:
                            child_dbo = self.load_by_key(dbo_col.key_type, child_json, dbo_col.base_class)
                        else:
                            child_dbo = self._load_class(child_json, dbo_col.base_class)()
                            self.load_json(child_dbo, child_json)
                        coll.append(child_dbo)
                    except AttributeError:
                        db_log("{0} json failed to load for coll {1} in {2}".format(child_json, dbo_col.field_name, unicode(dbo.dbo_id)))
            except KeyError:
                if dbo.dbo_key_type:
                    db_log("db: Object " + unicode(dbo.dbo_debug_key) + " json missing collection " + dbo_col.field_name)

        for dbo_ref in dbo.dbo_refs:
            try:
                ref_key = json_obj[dbo_ref.field_name]
                ref_obj = self.load_by_key(dbo_ref.key_type, ref_key, dbo_ref.base_class)
                setattr(dbo, dbo_ref.field_name, ref_obj)
            except:
                if dbo.dbo_key_type:
                    db_log("db: Object " + unicode(dbo.dbo_debug_key) + " json missing ref " + dbo_ref.field_name)
        dbo.on_loaded()
        return True
