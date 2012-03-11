'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display, DisplayLine
from dto.rootdto import RootDTO
from entity import Entity
from creature import Creature
from dialog import DialogDTO
from action import TARGET_PLAYER, TARGET_ACTION, TARGET_MSG_CLASS, TARGET_ENV

class Player(Creature):   
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level",)
     
    def __init__(self, name):
        self.target_class = TARGET_PLAYER
        self.dbo_id = name.lower()
        self.name = name.capitalize()
        self.target_id = name.lower(),
        
    def baptise(self, soul, inven, env):
        Entity.__init__(self, soul, inven, env)
        
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        matching_actions = self.match_actions(words)
        if not matching_actions and not retry:
            return self.parse("say " + command, True)   
        matches = self.match_targets(matching_actions)
        if not matches:
            feedback = "What?" 
        elif len(matches) == 1:
            action, verb, target = matches[0]
            message = action.create_message(self, verb, target, command)
            if not message.msg_class:
                feedback = message.payload
            else:
                feedback = target.receive(message)
            if message.broadcast:
                self.env.broadcast(self, target, message.broadcast)
                feedback = self.translate_broadcast(self, target, message.broadcast)
            if message.dialog:
                self.session.dialog = message.dialog
                feedback = DialogDTO(message.dialog)
            if not feedback:
                return RootDTO(silent=True)
            if isinstance(feedback, RootDTO):
                return feedback
        else:
            feedback = "Ambiguous Command"
        return Display(feedback)
    
    def match_actions(self, words):
        matching_actions = []
        for verb_size in range(1, len(words) + 1):
            verb = words[:verb_size]
            action_set = self.actions.get(verb)
            if action_set:
                matching_actions.extend([(action, verb, words[verb_size:]) for action in action_set])
        return matching_actions
        
    def match_targets(self, matching_actions):
        matches = []
        for action, verb, target_id in matching_actions:
            if action.target_class == TARGET_ACTION:
                matches.append((action, verb, target_id))
            elif action.target_class == TARGET_MSG_CLASS:
                target = self.target_ids.get(action.msg_class)
                if target:
                    matches.append((action, verb, target))
            elif action.target_class == TARGET_ENV:
                matches.append((action, verb, self.env))
            elif action.target_class & TARGET_ENV and not target_id:
                matches.append((action, verb, self.env))
            else:
                target = self.target_ids.get(target_id)
                if target and target.target_class & action.target_class:
                    matches.append(action, verb, target)
        return matches;
                     
    def match_messages(self, messages):
        for message in messages:
            for target in self.targets:
                if target.accepts(message):
                    yield(message, target)
    
    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)
            
    def display_line(self, text):
        self.session.display_line(DisplayLine(text))
    
    def register_channel(self, channel):
        self.register(channel, self.display_channel)
        
    def receive_broadcast(self, source, target, broadcast):
        self.display_line(self.translate_broadcast(source, target, broadcast))
                  
    def short_desc(self):
        return self.name
            
    def detach(self):
        Entity.detach(self)   
        self.session = None
        