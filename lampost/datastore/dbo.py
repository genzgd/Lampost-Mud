'''
Created on Mar 4, 2012

@author: Geoffrey
'''

class RootDBOMeta(type):
    def __new__(meta, class_name, bases, new_attrs): #@NoSelf
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if "RootDBO" in [base.__name__ for base in bases]:
            cls.dbo_base_class = cls
        return cls

class DBODict(dict):
    def append(self, dbo):
        self[dbo.dbo_id] = dbo
    
    def __iter__(self):
        return self.itervalues()
        
    def remove(self, dbo):
        del self[dbo.dbo_id]  

class RootDBO(object): 
    __metaclass__ = RootDBOMeta   
    dbo_key_type = None
    dbo_set_type = None
    dbo_set_id = None
    dbo_fields = ()
    dbo_collections = ()
    dbo_refs = ()
    dbo_id = None
    
    @property    
    def dbo_key(self):
        return ":".join([self.dbo_key_type, self.dbo_id])
    
    @property
    def dbo_set_key(self):
        if self.dbo_set_type:
            return self.dbo_set_type + ":" + self.dbo_set_id if self.dbo_set_id else ""
            
    def on_loaded(self):
        pass
        
    def before_save(self):
        pass
         
    def autosave(self):
        self.datastore.save_object(self, autosave=True);
        
         
    def describe(self, level=0, follow_refs=True):
        display = []
        
        def append(key, value):
            display.append(3 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp"  + str(value))
        
        if self.dbo_id:
            append("key", self.dbo_key)
        class_name =  self.__class__.__module__ + "." + self.__class__.__name__
        base_class_name = self.dbo_base_class.__module__ + "." + self.dbo_base_class.__name__
        if base_class_name != class_name:
            append("class", class_name)
        if self.dbo_set_key:
            append("set_key", self.dbo_set_key)
        for field in self.dbo_fields:
            append(field, getattr(self, field, "None"))
        
        for ref in self.dbo_refs:
            child_dbo = getattr(self, ref.field_name, None)
            if child_dbo:
                if follow_refs or not child_dbo.dbo_key_type:
                    display.extend(child_dbo.describe(level + 1))
                else:
                    append(ref.field_name, child_dbo.dbo_key)
            else:
                append(ref.field_name, "None")
        for col in self.dbo_collections:
            child_coll = getattr(self, col.field_name, None)
            if child_coll:
                append(col.field_name, "")
                for child_dbo in child_coll:
                    if follow_refs or not child_dbo.dbo_key_type:
                        display.extend(child_dbo.describe(level + 1, False))
                    else:
                        append(col.field_name, child_dbo.dbo_key)
            else:
                append(col.field_name, "None")
        return display
    
            
class DBORef():
    def __init__(self, field_name, base_class, key_type=None):
        self.field_name = field_name
        self.base_class = base_class
        self.key_type = key_type
        
