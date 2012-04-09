'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from dto.display import Display, DisplayLine

class RootDBO():    
    dbo_key_type = "global"
    dbo_set_type = None
    dbo_set_id = None
    dbo_fields = ()
    dbo_collections = ()
    dbo_refs = ()
    dbo_base_class = None
    
    def on_loaded(self):
        self.dbo_loaded = True 
    
    def get_dbo_key(self):
        return self.dbo_key_type + ":" + self.dbo_id
    
    def get_dbo_set_key(self):
        if self.dbo_set_type:
            return self.dbo_set_type + ":" + self.dbo_set_id if self.dbo_set_id else ""
        
    def describe(self, level=0):
        display = []
        results = []
        results.append(("key", self.get_dbo_key()))
        results.append(("set_key", self.get_dbo_set_key()))
        if self.dbo_base_class:
            results.append(("base_class", self.dbo_base_class.__module__ + "." + self.dbo_base_class.__name__))
        else:
            results.append(("base_class", "None"))
        for field in self.dbo_fields:
            results.append((field, getattr(self, field, "NULL")))
        for field in self.dbo_refs:
            pass
           
        for result in results:
            display.append((3 * level) * "&nbsp" + DisplayLine(result[0] + ":" + (16 - len(result[0])) * "&nbsp"  + str(result[1])))
        return display
    
    dbo_key = property(get_dbo_key)
    dbo_set_key = property(get_dbo_set_key)

        
class DBORef():
    def __init__(self, field_name, base_class, key_type, cascade=False):
        self.field_name = field_name
        self.base_class = base_class
        self.key_type = key_type
        self.cascade = cascade
        
class DBOCollection(DBORef):
    def __init__(self, field_name, base_class, key_type=None, cascade=True):
        DBORef.__init__(self, field_name, base_class, key_type, cascade)
        

        