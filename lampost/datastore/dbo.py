'''
Created on Mar 4, 2012

@author: Geoffrey
'''
class RootDBO():    
    dbo_key_type = "global"
    dbo_set_type = None
    dbo_set_id = None
    dbo_fields = ()
    dbo_collections = ()
    dbo_class_name = None
    
    def on_loaded(self):
        self.dbo_loaded = True 
    
    def get_dbo_key(self):
        return self.dbo_key_type + ":" + self.dbo_id
    
    def get_dbo_set_key(self):
        if self.dbo_set_type:
            return self.dbo_set_type + ":" + self.dbo_set_id if self.dbo_set_id else ""
    
    dbo_key = property(get_dbo_key)
    dbo_set_key = property(get_dbo_set_key)

        
class DBOCollection():
    def __init__(self, field_name, key_type, cascade=True):
        self.field_name = field_name
        self.key_type = key_type
        self.cascade = cascade
        