'''
Created on Mar 4, 2012

@author: Geoffrey
'''

from redis import ConnectionPool
from redis.client import StrictRedis
from json import JSONEncoder

class RedisStore():
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        pool = ConnectionPool(max_connections=2)
        self.redis = StrictRedis(connection_pool=pool)
        dispatcher.register("save_object", self.save_object)
        dispatcher.register("load_object", self.load_object)
        self.encoder = JSONEncoder()
       
    def save_object(self, dbo):
        dbo_def = dbo.__class__.DBODef
        json_obj = {}
        for field_name in dbo_def.fields:
            json_obj[field_name] = getattr(dbo, field_name)
        for dbo_col in dbo_def.collections:
            id_list = list()
            for child_dbo in getattr(dbo, dbo_col.name):
                child_key_type = child_dbo.__class__.DBODef.key_type
                id_list.append(child_key_type + ":" + child_dbo.dbo_id)
            json_obj[dbo_col] = id_list
        key = dbo_def.key_type + ":" + dbo.dbo_id
        self.redis.set(key, self.encoder.encode(json_obj))
        self.dispatcher.dispatch("db_log", "object saved: " + key)
    
    
    def load_object(self, dbo):
        pass
    
    def del_object(self, dbo):
        pass
