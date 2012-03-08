'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO

from message import CLASS_LEAVE_ROOM, LMessage, CLASS_ENTER_ROOM,\
    CLASS_COMM_GENERAL

class Entity(RootDBO):
    
    def register(self, event_type, callback):
        self.registrations.add(Entity.dispatcher.register(event_type, callback))
  
    def __init__(self, soul, inven, env):
        self.registrations = set()
        self.soul = soul
        self.inven = inven
        self.env = env
        self.env.receive(LMessage(self, CLASS_ENTER_ROOM, self))
        self.update_state()
    
    def accepts(self, lmessage):
        if lmessage.msg_class == CLASS_COMM_GENERAL:
            if lmessage.payload == self.target_id:
                return True
            if not lmessage.payload and lmessage.source == self:           
                return True
        
    def update_state(self):
        self.providers = set()
        self.add_providers((self.soul, self.inven, self.env))
        self.targets = set()
        self.add_targets((self.soul, self.inven, self.env))
        
    def add_providers(self, providers):
        for provider in providers:
            try:
                self.providers.update(provider.get_actions())
            except TypeError:
                try:
                    self.providers.add(provider.get_actions())
                except AttributeError:
                    pass
                except TypeError:
                    pass
            except AttributeError:
                pass
            try:    
                self.add_providers(provider.get_chidren())
            except TypeError:
                pass
            except AttributeError:
                pass
            
    def add_targets(self, targets):
        for target in targets:
            try:
                self.targets.update(target.get_targets())
            except TypeError:
                try:
                    self.targets.add(target.get_targets())
                except AttributeError:
                    pass
                except TypeError:
                    pass
            except AttributeError:
                pass
            try:    
                self.add_targets(target.get_children())
            except TypeError:
                pass
            except AttributeError:
                pass
    
    def get_targets(self):
        return self
    
    def change_env(self, new_env):
        self.env.receive(LMessage(self, CLASS_LEAVE_ROOM, self))
        self.env = new_env
        self.env.receive(LMessage(self, CLASS_ENTER_ROOM, self))
        self.update_state()
            
    def detach(self):
        self.env.receive(LMessage(self, CLASS_LEAVE_ROOM, self))
        for registration in self.registrations:
            registration.detach()

            
class Soul():
    def __init__(self):
        self.actions = set()
        self.targets = set()
        
    def get_actions(self):
        return self.actions
    
    def get_targets(self):
        return self.targets
