'''
Created on Apr 17, 2012

@author: Geoff
'''
from lampost.util.lmutil import pronouns
defaults = {'e':'s', 't':'e', 'st':'s', 'et':'e', 'sf':'s', 'ef':'e'}    

class BroadcastMap(object):
    
    def __init__(self, def_msg=None, **kwargs):
        self.s = def_msg;
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            
    def __getitem__(self, msg_key):
        while True:
            msg = getattr(self, msg_key, None)
            if msg:
                return msg
            msg_key = defaults[msg_key]
            if not msg_key:
                return "Invalid message type"
                
class Broadcast(object):
    def __init__(self, broadcast_map=None, source=None, target=None, color=0x000000, **kwargs):
        if broadcast_map:
            self.broadcast_map = broadcast_map
        else:
            self.broadcast_map = BroadcastMap(**kwargs)
        self.source = source
        self.target = target
        self.color = color
        self.broadcast = self
        
    def translate(self, observer):
        if not self.target:
            if not self.source or self.source == observer:
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
        return self.substitute('et')
            
    def substitute(self, version):
        message = self.broadcast_map[version]
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
    def __init__(self, source, all_msg, color=0x00000):
        self.source = source
        self.target = None
        self.all_msg = all_msg
        self.color = color
        self.broadcast = self
                
    def translate(self, observer):
        return self.all_msg
        
class EnvBroadcast():
    def __init__(self, source, self_msg, env_msg, color=0x000000):
        self.target = None
        self.source = source
        self.self_msg = self_msg
        self.env_msg = env_msg
        self.color = color
        self.broadcast = self
        
    def translate(self, observer):
        if self.source == observer:
            return self.self_msg
        return self.env_msg 