'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO

from message import CLASS_LEAVE_ROOM, LMessage, CLASS_ENTER_ROOM,\
    CLASS_SENSE_EXAMINE, CLASS_MOVEMENT, BC_ACTOR_NOTARG,\
    BC_ENV_NOTARG, BC_ACTOR_SELFTARG, BC_ACTOR_WTARG, BC_TARG, BC_ENV_WTARG,\
    BC_ENV_SELFTARG

import math

class Entity(RootDBO):
    
    def register(self, event_type, callback):
        self.registrations.add(Entity.dispatcher.register(event_type, callback))
  
    def __init__(self, soul, inven, env):
        self.env = env
        self.registrations = set()
        self.soul = soul
        self.inven = inven
        self.prefixes = ["red", "short"]
        self.suffix = None
        self.target_map = {}
        self.target_key_map = {}
        self.actions = {}
        self.add_target(self)
        for action in soul | inven:
            self.add_action(action)
        for target in inven:
            self.add_target(target, self)     
        self.enter_env(env)

    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_MOVEMENT:
            self.change_env(lmessage.payload)
        elif lmessage.msg_class == CLASS_LEAVE_ROOM:
            self.remove_target(lmessage.payload)
            self.remove_action(lmessage.payload)      
        elif lmessage.msg_class == CLASS_ENTER_ROOM:
            self.add_target(lmessage.payload, self.env)
            self.add_actions(lmessage.payload)
        elif lmessage.msg_class == CLASS_SENSE_EXAMINE:
            return self.short_desc() + ", a raceless, sexless, classless player."
    
    def add_targets(self, target, parent=None):
        self.add_target(target, parent)
        for child_target in target.get_children():
            self.add_target(child_target, target)
    
    def add_target(self, target, parent=None):
        try:
            target_id = target.name
            prefixes = list(target.prefixes)
            if isinstance(target_id, basestring):
                target_id = target_id.lower()
                if parent == self.env:
                    prefixes.insert(0, "the")
                elif parent == self.inven:
                    prefixes.insert(0, "my")
                target_keys = list(self.gen_ids(prefixes, target_id))
                add_numbers = True
            else:
                target_keys = [target.name]
                add_numbers = False
            final_keys = self.add_target_keys(target_keys, target, add_numbers)
            self.target_map[target] = final_keys    
        except AttributeError:
            pass
    
    def add_target_keys(self, target_keys, target, add_numbers):
        final_keys = []
        for target_key in target_keys:
            final_keys.append(target_key)
            key_values = self.target_key_map.get(target_key)
            if key_values:
                if add_numbers:
                    numbered_key = target_key + (str(len(key_values) + 1),)
                    final_keys.append(numbered_key)
            else:
                key_values = []
                self.target_key_map[target_key] = key_values
            key_values.append(target)
        return final_keys
    
    def gen_ids(self, prefixes, target_id):
        pcnt = len(prefixes)
        for x in range(0, int(math.pow(2, pcnt))):
            next_prefix = []
            for y in range(0, pcnt):
                if int(math.pow(2, y)) & x:
                    next_prefix.append(prefixes[y])
            yield tuple(next_prefix) + (target_id,)
            
    def remove_targets(self, target):
        for child_target in target.get_children():
            if child_target != self:
                self.remove_target(child_target)
                
    def remove_target(self, target):
        target_keys = self.target_map[target]
        for target_key in target_keys:
            key_values = self.target_key_map[target_key]
            key_values.remove(target)
            if not key_values:
                del self.target_key_map[target_key]
        del self.target_map[target]
    
    def add_actions(self, provider):
        self.add_action(provider)
        try:
            for child_provider in provider.get_children():
                self.add_actions(child_provider)
        except AttributeError:
            pass
    
    def add_action(self, provider):
        try:
            for verb in provider.verbs:
                bucket = self.actions.get(verb)
                if not bucket:
                    bucket = set()
                    self.actions[verb] = bucket
                bucket.add(provider)
        except AttributeError:
            pass
           
    def remove_actions(self, provider):
        self.remove_action(provider)
        try:
            for child_provider in provider.get_children():
                self.remove_action(child_provider)
        except AttributeError:
            pass
            
    def remove_action(self, provider):
        try:
            for verb in provider.verbs:
                bucket = self.actions.get(verb)
                bucket.remove(provider)
                if len(set) == 0:
                    del self.actions[verb]
        except AttributeError:
            pass
        
    def change_env(self, new_env):
        self.remove_actions(self.env)
        self.remove_targets(self.env)
        self.env.receive(LMessage(self, CLASS_LEAVE_ROOM, self, "{p} leaves."))
        self.enter_env(new_env)
        
    def enter_env(self, new_env):
        self.env = new_env
        self.add_actions(new_env)      
        self.add_targets(new_env)
        self.env.receive(LMessage(self, CLASS_ENTER_ROOM, self, "{p} arrives."))
            
    def detach(self):
        self.env.receive(LMessage(self, CLASS_LEAVE_ROOM, self))
        for registration in self.registrations:
            registration.detach()
            
    def translate_broadcast(self, source, target, broadcast):
        
        pname = source.name
        if isinstance(broadcast, basestring):
            return broadcast.format(p=pname) 
        if len(broadcast) < 3:
            if source == self:
                version = BC_ACTOR_NOTARG
            else:
                version = BC_ENV_NOTARG
            return broadcast[version].format(p=pname)

        tname = target.name 
        if source == self:
            if target == self:
                version = BC_ACTOR_SELFTARG
            else:
                version = BC_ACTOR_WTARG
        elif target == self:
            version = BC_TARG
        elif target != source:
            version = BC_ENV_WTARG
        else:
            version = BC_ENV_SELFTARG
       
        return broadcast[version].format(p=pname, t=tname, pself="themself")