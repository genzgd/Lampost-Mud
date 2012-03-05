'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display, DisplayLine
from dto.rootdto import RootDTO
from entity import Entity
from message import CLASS_MOVEMENT, CLASS_LEAVE_ROOM, CLASS_ENTER_ROOM,\
    CLASS_COMM_GENERAL
from creature import Creature

class Player(Creature):   
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level",)
     
    def __init__(self, name):
        self.dbo_id = name.lower()
        self.name = name.capitalize()
        
    def baptise(self, soul, inven, env):
        Entity.__init__(self, soul, inven, env)
        
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        messages = list(self.match_actions(words, command))
        if not len(messages) and not retry:
            return self.parse("say " + command, True)   
        matches = list(self.match_messages(messages))
        if not matches:
            feedback = "What?" 
        elif len(matches) == 1:
            message, target = matches[0]
            feedback = target.receive(message)
            if message.to_self:
                feedback = self.receive(message)
            if not feedback:
                return RootDTO(silent=True)
            if isinstance(feedback, RootDTO):
                return feedback
        else:
            feedback = "Ambiguous Command"
        return Display(feedback)
    
    def match_actions(self, words, command):
        for action in self.providers:
            message = action.match(self, words, command=command)
            if message:
                yield(message)
    
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
        self.registrations.add(self.register(channel, self.display_channel))
        
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_MOVEMENT:
            self.change_env(lmessage.payload)
        elif lmessage.msg_class == CLASS_LEAVE_ROOM:
            if lmessage.source != self:
                self.display_line(lmessage.source.name + " leaves.")
        elif lmessage.msg_class == CLASS_ENTER_ROOM:
            if lmessage.source != self:
                self.display_line(lmessage.source.name + " arrives.")
        elif lmessage.msg_class == CLASS_COMM_GENERAL:
            if lmessage.source == self:
                return Display(lmessage.payload.self_text())
            self.display_line(lmessage.payload.other_text())
                
    def short_desc(self):
        return self.name
            
    def detach(self):
        Entity.detach(self)   
        self.session = None
        
    