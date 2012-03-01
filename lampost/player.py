'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display
from dto.rootdto import RootDTO
from entity import Entity

class Player(Entity):   
    @staticmethod
    def register(event_type, callback):
        return Player.dispatcher.register(event_type, callback)
    
    def __init__(self, name, session):
        self.session = session     
        self.name = name
        
    def baptise(self, soul, inven, env):
        Entity.__init__(self, soul, inven, env)
        
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        matches = list(self.parse_actions(words))
        if not matches:
            if not retry:
                return self.parse("say " + command, True)
            return Display("What?") 
        if len(matches) == 1:
            action, responder, verb, subject = matches[0]
            message = action.create_message(self, verb, subject)
            feedback = responder.receive(self, message)
            return feedback if feedback else RootDTO(silent=True)
        return Display("Ambiguous Command")
    
    def parse_actions(self, words):
        for action in self.providers:
            verb, subject = action.match(words)
            if verb:
                for target in self.targets:
                    if target.accepts(action, subject):
                        yield(action, target, verb, subject)
    
    def display_channel(self, message):
        if (message.originator != self):
            self.session.display_line(message.display_line)
    
    def register_channel(self, channel):
        self.registrations.add(self.register(channel, self.display_channel))
    
    def detach(self):
        Entity.detach(self)   
        self.session = None
        
        
    
           
            