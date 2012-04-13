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
from parse import KeyData

class Entity(RootDBO):
      
    def baptise(self, soul, inven, env):
        self.env = env
        self.registrations = set()
        self.soul = soul
        self.inven = inven
        self.prefixes = []
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

    def register(self, event_type, callback):
        self.registrations.add(Entity.dispatcher.register(event_type, callback))
        
    def register_p(self, freq, callback):
        self.registrations.add(Entity.dispatcher.register_p(freq, callback))

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
            try:
                target_id = target_id.lower()
                prefixes = list(target.prefixes)
                if parent == self.env:
                    prefixes.insert(0, "the")
                elif parent == self.inven:
                    prefixes.insert(0, "my")
                target_keys = list(self.gen_ids(prefixes, target_id))
                add_numbers = True
            except:
                target_keys = [target.name]
                add_numbers = False
            self.add_target_keys(target_keys, target, add_numbers)
        except AttributeError:
            pass
    
    def add_target_keys(self, target_keys, target, add_numbers):
        self.target_map[target] = []
        for target_key in target_keys:
            self.target_map[target].append(target_key)
            key_data = self.target_key_map.get(target_key)
            if key_data:
                if add_numbers:
                    new_count = key_data.count + 1
                    if new_count == 2:
                        self.target_key_map[target_key + ("1",)] = KeyData(key_data.values[0])
                    key_data.count = new_count
                    self.target_key_map[target_key + (str(new_count),)] = KeyData(target);
            else:
                key_data = KeyData()
                self.target_key_map[target_key] = key_data
            key_data.values.append(target)
   
    
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
            key_data = self.target_key_map[target_key]
            if key_data.count == 1:
                del self.target_key_map[target_key]
            else:
                target_loc = key_data.values.index(target)
                key_data.values.pop(target_loc)
                self.renumber_keys(target_key, key_data)
        del self.target_map[target]
    
    def renumber_keys(self, target_key, key_data):
        for ix in range(0, key_data.count):
            number_key = target_key + (str(ix + 1),)
            del self.target_key_map[number_key]
        key_data.count = len(key_data.values)  
        if key_data.count < 2:
            return
        for ix in range(0, key_data.count):
            number_key = target_key + (str(ix + 1),)
            self.target_key_map[number_key] = KeyData(key_data.values[ix])
            
    
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
                if len(bucket) == 0:
                    del self.actions[verb]
        except AttributeError:
            pass
        
    def refresh_env(self):
        self.change_env(self.env)    
        
    def change_env(self, new_env):
        self.leave_env()
        self.enter_env(new_env)
        
    def leave_env(self):
        if self.env:
            self.remove_actions(self.env)
            self.remove_targets(self.env)
            self.env.receive(LMessage(self, CLASS_LEAVE_ROOM, self, "{p} leaves."))
        
    def enter_env(self, new_env):
        self.env = new_env
        self.room_id = new_env.dbo_id
        self.add_actions(new_env)      
        self.add_targets(new_env)
        self.env.receive(LMessage(self, CLASS_ENTER_ROOM, self, "{p} arrives."))
            
    def detach(self):
        for registration in self.registrations:
            registration.detach()
            
    def translate_broadcast(self, source, target, broadcast):
        pname = source.name
        try:
            return broadcast.format(p=pname)
        except:
            pass
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