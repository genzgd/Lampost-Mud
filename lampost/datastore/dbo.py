'''
Created on Mar 4, 2012

@author: Geoffrey
'''

class RootDBO(object):    
    dbo_key_type = None
    dbo_set_type = None
    dbo_set_id = None
    dbo_fields = ()
    dbo_collections = ()
    dbo_refs = ()
    dbo_base_class = None
    dbo_id = None
       
    @property    
    def dbo_key(self):
        return self.dbo_key_type + ":" + self.dbo_id
    
    @property
    def dbo_set_key(self):
        if self.dbo_set_type:
            return self.dbo_set_type + ":" + self.dbo_set_id if self.dbo_set_id else ""
            
    def on_loaded(self):
        pass
         
    def auto_save(self):
        self.datastore.save_object(self);
        
    def apply_template(self, instance):
        for field in self.dbo_fields:
            setattr(instance, getattr(self, field, "None"))
        
    def describe(self, level=0, follow_refs=True):
        display = []
        def append(key, value):
            display.append(3 * level * "&nbsp" + key + ":" + (16 - len(key)) * "&nbsp"  + str(value))
        if self.dbo_id:
            append("key", self.get_dbo_key())
        append("class", self.__class__.__module__ + "." + self.__class__.__name__)
        if self.get_dbo_set_key():
            append("set_key", self.get_dbo_set_key())
        if self.dbo_base_class:
            append("base_class", self.dbo_base_class.__module__ + "." + self.dbo_base_class.__name__)
        for field in self.dbo_fields:
            append(field, getattr(self, field, "None"))
        for ref in self.dbo_refs:
            child_dbo = getattr(self, ref.field_name, None)
            if child_dbo:
                if follow_refs:
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
                    if follow_refs:
                        display.extend(child_dbo.describe(level + 1, False))
                    else:
                        append(3 * "&nbsp", child_dbo.dbo_key)
            else:
                append(col.field_name, "None")
        return display
    
        
class DBORef():
    def __init__(self, field_name, base_class, key_type, cascade=False):
        self.field_name = field_name
        self.base_class = base_class
        self.key_type = key_type
        self.cascade = cascade
        
            
class DBOCollection(DBORef):
    def __init__(self, field_name, base_class, key_type=None, cascade=True):
        DBORef.__init__(self, field_name, base_class, key_type, cascade)
        

        