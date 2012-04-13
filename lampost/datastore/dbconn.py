'''
Created on Mar 4, 2012

@author: Geoffrey
'''

from redis import ConnectionPool
from redis.client import StrictRedis
from json import JSONEncoder
from json.decoder import JSONDecoder

class RedisStore():
    def __init__(self, dispatcher, db_host, db_port, db_num, db_pw):
        self.dispatcher = dispatcher
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port, password=db_pw)
        self.redis = StrictRedis(connection_pool=pool)
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()
        self.class_map = {}
        self.object_map = {}
            
    def save_object(self, dbo, update_rev=False):
        if update_rev:
            dbo.dbo_rev = getattr(dbo, "dbo_rev", 0) + 1
        json_obj = self.build_json(dbo)
        key = dbo.dbo_key
        self.redis.set(key, self.encoder.encode(json_obj))
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, key)
        dbo.dbo_loaded = True
        self.dispatcher.dispatch("db_log", "object saved: " + key)
        self.object_map[dbo.dbo_key] = dbo;
        return True
    
    def build_json(self, dbo):
        json_obj = {}
        if dbo.__class__ != dbo.dbo_base_class:
            json_obj["class_name"] = dbo.__module__ + "." + dbo.__class__.__name__
        for field_name in dbo.dbo_fields:
            json_obj[field_name] = getattr(dbo, field_name)
        for dbo_col in dbo.dbo_collections:
            coll_list = list()
            for child_dbo in getattr(dbo, dbo_col.field_name):
                if dbo_col.key_type:
                    coll_list.append(child_dbo.dbo_id)
                    if dbo_col.cascade:
                        self.save_object(child_dbo)    
                else:
                    coll_list.append(self.build_json(child_dbo))
            json_obj[dbo_col.field_name] = coll_list
        for dbo_ref in dbo.dbo_refs:
            ref = getattr(dbo, dbo_ref.field_name, None)
            if ref:
                json_obj[dbo_ref.field_name] = ref.dbo_id   
        return json_obj
    
    def cache_object(self, dbo):
        self.object_map[dbo.dbo_key]
    
    def load_cached(self, key):
        return self.object_map.get(key)
    
    def evict(self, dbo):
        try:
            del self.object_map[dbo.dbo_key]
        except:
            self.dispatcher.dispatch("db_log", "Failed to evict " + dbo.dbo_key + " from db cache")
                
    def load_by_key(self, key_type, key, base_class=None):
        dbo_key = key_type + ":" + key
        cached_dbo = self.object_map.get(dbo_key)
        if cached_dbo:
            return cached_dbo
        json_str = self.redis.get(dbo_key)
        if not json_str:
            return None
        json_obj = self.decoder.decode(json_str)
        dbo = self.load_class(json_obj, base_class)(key)
        if dbo.dbo_key_type:
            self.object_map[dbo.dbo_key] = dbo
        self.load_json(dbo, json_obj)
        return dbo
        
    def load_class(self, json_obj, base_class):
        class_path = json_obj.get("class_name")
        if not class_path:
            return base_class
        clazz = self.class_map.get(class_path)
        if clazz:
            return clazz
        split_path = class_path.split(".")
        module_name = ".".join(split_path[:-1])
        class_name = split_path[-1]
        module = __import__(module_name, globals(), locals(), [class_name])
        clazz = getattr(module, class_name)
        self.class_map[class_path] = clazz
        return clazz 
    
    def load_object(self, dbo_class, key):
        return self.load_by_key(dbo_class.dbo_key_type, key, dbo_class)
    
    def load_json(self, dbo, json_obj):
        
        for field_name in dbo.dbo_fields:
            try:
                setattr(dbo, field_name, json_obj[field_name])
            except KeyError:
                self.dispatcher.dispatch("db_log", "db: Object " + dbo.dbo_key + " json missing field " + field_name)
        for dbo_col in dbo.dbo_collections:
            if not dbo_col.cascade:
                continue
            coll = getattr(dbo, dbo_col.field_name, [])
            try:
                for child_json in json_obj[dbo_col.field_name]:
                    if dbo_col.key_type:
                        child_dbo = self.load_by_key(dbo_col.key_type, child_json, dbo_col.base_class)
                    else:
                        child_dbo = self.load_class(child_json, dbo_col.base_class)()
                        self.load_json(child_dbo, child_json)
                    coll.append(child_dbo)
            except KeyError:
                self.dispatcher.dispatch("db_log", "db: Object " + dbo.dbo_key + " json missing collection " + dbo_col.field_name)
        
        for dbo_ref in dbo.dbo_refs:
            try:
                ref_key = json_obj[dbo_ref.field_name]
                ref_obj = self.load_by_key(dbo_ref.key_type, ref_key, dbo_ref.base_class)
                setattr(dbo, dbo_ref.field_name, ref_obj)    
            except:
                self.dispatcher.dispatch("db_log", "db: Object " + dbo.dbo_key + " json missing ref " + dbo_ref.field_name)
            
        return True
                    
    def delete_object(self, dbo):
        key = dbo.dbo_key
        self.redis.delete(key)
        if dbo.dbo_set_key:
            self.redis.srem(dbo.dbo_set_key, key)
        for dbo_col in dbo.dbo_collections:
            if dbo_col.cascade and dbo_col.key_type:
                coll = getattr(dbo, dbo_col.field_name, set())
                for child_dbo in coll:
                    self.delete_object(child_dbo)
        self.dispatcher.dispatch("db_log", "object deleted: " + key)
        if self.object_map.get(dbo.dbo_key):
            del self.object_map[dbo.dbo_key]
        return True
        
    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)
