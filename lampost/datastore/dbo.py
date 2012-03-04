'''
Created on Mar 4, 2012

@author: Geoffrey
'''
class DBODef():
    def __init__(self, key_type, fields=None, collections=None):
        self.key_type = key_type
        if fields is None:
            fields = ()
        if collections is None:
            collections = ()
        self.fields = set(fields)
        self.collections = set(collections)
        
class DBOCollection():
    def __init__(self, name, cascade=False):
        self.name = name
        self.cascade = cascade
        