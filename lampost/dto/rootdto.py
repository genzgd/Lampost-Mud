'''
Created on Feb 19, 2012

@author: Geoff
'''
from json import JSONEncoder

class DTOEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, RootDTO):
            return o.raw
        return JSONEncoder.default(self, o)

class RootDTO(): 
    def __init__(self, **kw):
        self.merge_dict(kw);
        
    def merge(self, other):
        self.merge_dict(other.raw)
        return self
            
    def merge_dict(self, dictionary):
        for key, value in dictionary.iteritems():
            peer = getattr(self, key, None)
            if peer:
                if isinstance(peer, list):
                    peer.extend(value)
                elif isinstance(peer, RootDTO):
                    peer.merge(value)
            else:
                setattr(self, key, value)              
        return self
     
    def get_json(self):
        return RootDTO.__encoder__.encode(self)
    
    def get_dict(self):
        raw = {}
        for key, value in self.__dict__.iteritems():
            raw[key] = value
        return raw
       
   
    __encoder__ = DTOEncoder()     
    json = property(get_json)
    raw = property(get_dict)

    