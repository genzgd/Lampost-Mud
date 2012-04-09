'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import DisplayLine
from entity import Entity
from creature import Creature
from dialog import DialogDTO
from action import TARGET_PLAYER, TARGET_ACTION, TARGET_MSG_CLASS, TARGET_ENV,\
    TARGET_SELF

class Player(Creature):   
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level", "room_id")
     
    def __init__(self, name):
        self.target_class = TARGET_PLAYER
        self.dbo_id = name.lower()
        self.name = name.capitalize()
        self.last_tell = None
              
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        matching_actions = self.match_actions(words)
        if not matching_actions and not retry:
            return self.parse("say " + command, True)   
        matches = self.match_targets(matching_actions)
        if not matches:
            return "What?"
        if len(matches) > 1:
            return "Ambiguous command."
         
        action, verb, target = matches[0]
        message = action.create_message(self, verb, target, command)
        try:
            feedback = target.receive(message)
        except:
            feedback = message
        try:
            if message.broadcast:
                if target != self.env:
                    self.env.broadcast(self, target, message.broadcast)
                feedback = self.translate_broadcast(self, target, message.broadcast)
        except:
            pass
        try:
            if message.dialog:
                self.session.dialog = message.dialog
                feedback = DialogDTO(message.dialog)
        except:
            pass
        return feedback
     
    def match_actions(self, words):
        matching_actions = []
        for verb_size in range(1, len(words) + 1):
            verb = words[:verb_size]
            action_set = self.actions.get(verb)
            if action_set:
                for action in action_set:
                    target_id = action.msg_class if action.action_class == TARGET_MSG_CLASS else words[verb_size:]
                    matching_actions.append((action, verb, target_id))
        return matching_actions
        
    def match_targets(self, matching_actions):
        matches = []
        for action, verb, target_id in matching_actions:
            if action.action_class == TARGET_ACTION:
                matches.append((action, verb, target_id))
            elif action.action_class == TARGET_ENV:
                matches.append((action, verb, self.env))
            elif action.action_class & TARGET_ENV and not target_id:
                matches.append((action, verb, self.env))
            else:
                key_data = self.target_key_map.get(target_id)
                if not key_data:
                    continue
                for target in key_data.values:
                    if  (action.action_class == TARGET_SELF and target == action) or (target.target_class & action.action_class):
                        matches.append((action, verb, target))
        return matches;
                     
    def match_messages(self, messages):
        for message in messages:
            for target in self.targets:
                if target.accepts(message):
                    yield(message, target)
    
    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)
            
    def display_line(self, text, color=0x000000):
        self.session.display_line(DisplayLine(text, color))
    
    def register_channel(self, channel):
        self.register(channel, self.display_channel)
        
    def receive_broadcast(self, source, target, broadcast):
        self.display_line(self.translate_broadcast(source, target, broadcast))
                  
    def short_desc(self):
        return self.name
            
    def detach(self):
        Entity.detach(self)   
        self.session = None
        
Player.dbo_base_class = Player
        