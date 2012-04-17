'''
Created on Feb 17, 2012

@author: Geoff
'''
from lmutil import pronouns
        
class Broadcast(object):
    def __init__(self, message_map, source=None, target=None, color=0x000000):
        self.message_map = message_map
        self.source = source
        self.target = target
        self.color = color
        self.broadcast = self
        
    def translate(self, observer):
        if not self.target and not self.source:
            return self.substitute('s')
        if self.target == self.source:
            if self.source == observer:
                return self.substitute('sf')
            return self.substitute('ef')
        if self.target == observer:
            return self.substitute('t')
        if not self.target:
            return self.substitute('e')
        if self.source == observer:
            return self.substitute('st')
        return self.substiteu('et')
            
    def substitute(self, version):
        message = self.message_map[version]
        if self.source:
            sname = self.source.name
            ssub, sobj, sposs, sself = pronouns(self.source.sex)
        else:
            sname = ssub = sobj = sposs = sself = None
        if self.target:
            tname = self.target.name
            tsub, tobj, tposs, tself = pronouns(self.target.sex)
        else:
            tname = tsub = tobj = tposs = tself = None
       
        return message.format(n=sname, N=tname, e=ssub, E=tsub, \
            s=sposs, S=tposs, m=sobj, M=tobj, f=sself, F=tself)
            
class SingleBroadcast():
    def __init__(self, all_msg, color=0x00000):
        self.all_msg = all_msg
        self.color = color
        self.broadcast = self
                
    def translate(self, observer):
        return self.all_msg
        
class SimpleBroadcast():
    def __init__(self, source, self_msg, env_msg, color=0x000000):
        self.self_msg = self_msg
        self.env_msg = env_msg
        self.color = color
        self.broadcast = self
        
    def translate(self, observer):
        if self.source == observer:
            return self.self_msg
        return self.env_msg

class Action():
    imm_level = 0
    mud = None

    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data) 
        
    @staticmethod
    def save_object(obj, update_rev=False):
        return Action.datastore.save_object(obj, update_rev)
        
    @staticmethod
    def create_object(obj):
        return Action.datastore.create_object(obj)
        
    @staticmethod
    def load_object(obj_class, key):
        return Action.datastore.load_object(obj_class, key)
        
    @staticmethod
    def delete_object(obj):
        return Action.datastore.delete_object(obj)          
    
    def __init__(self, verbs, msg_class=None):
        self.verbs = set()
        try:
            self.add_verb(verbs)
        except AttributeError:
            for verb in verbs:
                self.add_verb(verb)
        self.msg_class = msg_class
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))    

