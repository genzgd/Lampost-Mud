'''
Created on Mar 4, 2012

@author: Geoffrey
'''

from redis import ConnectionPool
from redis.client import StrictRedis
from json import JSONEncoder
from json.decoder import JSONDecoder

class RedisStore():
    def __init__(self, dispatcher, db_host, db_port, db_num):
        self.dispatcher = dispatcher
        pool = ConnectionPool(max_connections=2, db=db_num, host=db_host, port=db_port)
        self.redis = StrictRedis(connection_pool=pool)
        dispatcher.register("save_object", self.save_object)
        dispatcher.register("load_object", self.load_object)
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()
        self.class_map = {}
        self.object_map = None
        
    def start_session(self):
        self.object_map = {}
        
    def end_session(self):
        self.object_map = None
    
    def save_object(self, dbo):
        json_obj = self.build_json(dbo)
        key = dbo.dbo_key
        self.redis.set(key, self.encoder.encode(json_obj))
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, key)
        dbo.dbo_loaded = True
        self.dispatcher.dispatch("db_log", "object saved: " + key)
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
        return json_obj
                
    def load_by_key(self, key_type, key, base_class):
        json_str = self.redis.get(key_type + ":" + key)
        json_obj = self.decoder.decode(json_str)
        dbo = self.load_class(json_obj, base_class)(key)
        self.load_object(dbo, json_obj)
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
    
    def hydrate_object(self, dbo):
        json_str = self.redis.get(dbo.dbo_key)
        if not json_str:
            return False
        json_obj = self.decoder.decode(json_str)
        return self.load_object(dbo, json_obj)
    
    def load_object(self, dbo, json_obj):
        try:
            for field_name in dbo.dbo_fields:
                setattr(dbo, field_name, json_obj[field_name])
        except KeyError:
            pass
        for dbo_col in dbo.dbo_collections:
            if not dbo_col.cascade:
                continue
            coll = getattr(dbo, dbo_col.field_name, set())
            for child_json in json_obj[dbo_col.field_name]:
                if dbo_col.key_type:
                    child_dbo = self.load_by_key(dbo_col.key_type, child_json, dbo_col.base_class)
                else:
                    child_dbo = self.load_class(dbo_col.base_class)
                coll.append(child_dbo)
        dbo.on_loaded()
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
        return True
        
    def fetch_set_keys(self, set_key):
        return self.redis.smembers(set_key)
