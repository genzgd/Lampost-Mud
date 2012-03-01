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
        matches = list(self.parse_actions(words, command))
        if not matches:
            if not retry:
                return self.parse("say " + command, True)
            feedback = "What?" 
        elif len(matches) == 1:
            message, target = matches[0]
            feedback = target.receive(message)
            if not feedback:
                return RootDTO(silent=True)
            if isinstance(feedback, RootDTO):
                return feedback
        else:
            feedback = "Ambiguous Command"
        return Display(feedback)
    
    def parse_actions(self, words, command):
        for action in self.providers:
            message = action.match(self, words, command)
            if message:
                for target in self.targets:
                    if target.accepts(message):
                        yield(message, target)
    
    def display_channel(self, message):
        if (message.source != self):
            self.session.display_line(message.display_line)
    
    def register_channel(self, channel):
        self.registrations.add(self.register(channel, self.display_channel))
    
    def detach(self):
        Entity.detach(self)   
        self.session = None
        
        
    
           
            