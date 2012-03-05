'''
Created on Mar 4, 2012

@author: Geoffrey
'''

from redis import ConnectionPool
from redis.client import StrictRedis
from json import JSONEncoder
from json.decoder import JSONDecoder

class RedisStore():
    def __init__(self, dispatcher, db_num):
        self.dispatcher = dispatcher
        pool = ConnectionPool(max_connections=2, db=db_num)
        self.redis = StrictRedis(connection_pool=pool)
        dispatcher.register("save_object", self.save_object)
        dispatcher.register("load_object", self.load_object)
        self.encoder = JSONEncoder()
        self.decoder = JSONDecoder()
       
    def save_object(self, dbo):
        json_obj = {}
        for field_name in dbo.dbo_fields:
            json_obj[field_name] = getattr(dbo, field_name)
        for dbo_col in dbo.dbo_collections:
            id_list = list()
            for child_dbo in getattr(dbo, dbo_col.field_name):
                id_list.append(child_dbo.dbo_id)
            json_obj[dbo_col] = id_list
        key = dbo.dbo_key
        self.redis.set(key, self.encoder.encode(json_obj))
        if dbo.dbo_set_key:
            self.redis.sadd(dbo.dbo_set_key, key)
        dbo.dbo_loaded = True
        self.dispatcher.dispatch("db_log", "object saved: " + key)
    
    def load_object(self, dbo):
        json_str = self.redis.get(dbo.dbo_key)
        if not json_str:
            return False
        json_obj = self.decoder.decode(json_str)
        for field_name in dbo.dbo_fields:
            setattr(dbo, field_name, json_obj[field_name])
        for dbo_col in dbo.dbo_collections:
            if not dbo_col.cascade:
                continue
            coll = getattr(dbo, dbo_col.field_name, set())
            for dbo_id in json_obj[dbo_col.field_name]:
                child_dbo = dbo_col.field_class.__new__(dbo_id)
                self.load_object(child_dbo)
                coll.append(child_dbo)
        dbo.on_loaded()
        return True
                    
    def del_object(self, dbo):
        pass
