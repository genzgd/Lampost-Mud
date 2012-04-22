'''
Created on Feb 26, 2012

@author: Geoff
'''
import math
from lampost.coreobj.lmlog import debug
from item import BaseItem
from broadcast import Broadcast

class Entity(BaseItem):
    env = None
    entry_msg = Broadcast(s="{n} arrives.")
    exit_msg = Broadcast(s="{n} leaves.")
      
    def baptise(self, soul):
        self.registrations = set()
        self.soul = soul        
        self.target_map = {}
        self.target_key_map = {}
        self.actions = {}
        self.add_target_keys([(self.target_id,)], self) 
        for action in soul:
            self.add_action(action)
        
    def equip(self, inven):
        self.inven = inven
        for action in inven:
            self.add_action(action)
        for target in inven:
            self.add_target(target, self)
            
    def enhance_soul(self, actions):
        for action in actions:
            self.add_action(action)
        self.soul.update(set(actions))    
 
    def rec_entity_enter_env(self, entity):
        self.add_target(entity, self.env)
        self.add_actions(entity)
    
    def rec_entity_leave_env(self, entity):
        self.remove_target(entity)
        self.remove_action(entity)
                
    def add_targets(self, target, parent=None):
        self.add_target(target, parent)
        for child_target in getattr(target, "children", []):
            self.add_target(child_target, target)
    
    def add_target(self, target, parent=None):
        if target == self:
            return
        try:
            target_id = target.target_id
        except AttributeError:
            return
        if self.target_map.get(target):  #Should not happen
            debug("Trying to add " + str(target_id) + " more than once")
            return    
        target_id = target_id.lower()
        prefixes = list(target.prefixes)
        if parent == self.env:
            prefixes.insert(0, "the")
        elif parent == self.inven:
            prefixes.insert(0, "my")
        target_keys = list(self.gen_ids(prefixes, target_id))
        self.add_target_keys(target_keys, target)
    
    
    def add_target_keys(self, target_keys, target):
        self.target_map[target] = []
        for target_key in target_keys:
            self.target_map[target].append(target_key)
            key_data = self.target_key_map.get(target_key)
            if key_data:
                key_data.append(target)
                new_count = len(key_data)
                if new_count == 2:
                    self.target_key_map[target_key + ("1",)] = [key_data[0]]
                self.target_key_map[target_key + (unicode(new_count),)] = [target];
            else:
                self.target_key_map[target_key] = [target]
            

    def gen_ids(self, prefixes, target_id):
        pcnt = len(prefixes)
        for x in range(0, int(math.pow(2, pcnt))):
            next_prefix = []
            for y in range(0, pcnt):
                if int(math.pow(2, y)) & x:
                    next_prefix.append(prefixes[y])
            yield tuple(next_prefix) + (target_id,)
            
    def remove_targets(self, target):
        self.remove_target(target)
        for child_target in getattr(target, "children", []):
            self.remove_target(child_target)
                
    def remove_target(self, target):
        if self == target:
            return
        target_keys = self.target_map.get(target, None)
        if not target_keys:
            return
        del self.target_map[target]
        for target_key in target_keys:
            key_data = self.target_key_map[target_key]
            if len(key_data) == 1:
                del self.target_key_map[target_key]
            else:
                target_loc = key_data.index(target)
                key_data.pop(target_loc)
                self.renumber_keys(target_key, key_data)
       
    
    def renumber_keys(self, target_key, key_data):
        for ix in range(len(key_data) + 1):
            number_key = target_key + (unicode(ix + 1),)
            del self.target_key_map[number_key]
        if len(key_data) < 2:
            return
        for ix, target in enumerate(key_data):
            self.target_key_map[target_key + (unicode(ix + 1),)] = [target]
            
    
    def add_actions(self, provider):
        self.add_action(provider)
        for child_provider in getattr(provider, "children", []):
            self.add_actions(child_provider)
    
    def add_action(self, provider):
        for verb in getattr(provider, "verbs", []):
            bucket = self.actions.get(verb)
            if not bucket:
                bucket = set()
                self.actions[verb] = bucket
            bucket.add(provider)
           
    def remove_actions(self, provider):
        self.remove_action(provider)
        for child_provider in getattr(provider, "children", []):
            self.remove_action(child_provider)
       
            
    def remove_action(self, provider):
        for verb in getattr(provider, "verbs", []):
            bucket = self.actions.get(verb)
            bucket.remove(provider)
            if len(bucket) == 0:
                del self.actions[verb]
        
            
    def parse_command(self, command):
        words = tuple(command.lower().split())
        matches = list(self.match_actions(words))
        if not matches:
            return None, None
        if len(matches) > 1:
            return matches, None    
        action, verb, args, target, target_method = matches[0]
        return matches, action.execute(source=self, target=target, verb=verb, args=args,
            target_method=target_method, command=command)
  
              
    def match_actions(self, words):
        for verb_size in range(1, len(words) + 1):
            verb = words[:verb_size]
            args = words[verb_size:]    
            for action in self.actions.get(verb, []):
                msg_class = getattr(action, "msg_class", None)
                fixed_targets = getattr(action, "fixed_targets", None)
                if msg_class:           
                    for target, target_method in self.matching_targets(args, msg_class):
                        if not fixed_targets or target in fixed_targets:
                            yield action, verb, args, target, target_method
                else:
                    yield action, verb, args, action, None
                            
    def matching_targets(self, target_args, msg_class):
        for target in self.target_key_map.get(target_args, []) if target_args else [self.env]:
            target_method = target_method = getattr(target, msg_class, None)
            if target_method:
                yield target, target_method
                      
    def refresh_env(self):
        self.change_env(self.env)
        
    def change_env(self, new_env):
        self.leave_env()
        self.enter_env(new_env)
        
    def leave_env(self):
        if self.env:
            self.remove_actions(self.env)
            self.remove_targets(self.env)
            self.env.rec_entity_leaves(self)
        
    def enter_env(self, new_env):
        self.env = new_env
        self.room_id = new_env.room_id
        self.add_actions(new_env)      
        self.add_targets(new_env)
        self.env.rec_entity_enters(self)
            
    def detach(self):
        self.env = None
        for registration in self.registrations:
            registration.detach()
            
    def broadcast(self, broadcast):
        pass
