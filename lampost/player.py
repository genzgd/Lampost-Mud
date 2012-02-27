'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display
from dto.rootdto import RootDTO

class Player():   
    @staticmethod
    def register(event_type, callback):
        Player.dispatcher.register(event_type, callback)
    
    def __init__(self, name, session):
        self.session = session
        self.registrations = set()
        self.name = name
        self.soul = set()
        self.world = set()
        self.providers = [self.soul, self.world]
        
    def parse(self, command):
        matches = [action for provider in self.providers for action in provider if action.match(command)]
        if len(matches) == 1:
            feedback = matches[0].invoke(self, command); 
            if feedback:
                return feedback
            return RootDTO(silent=True)
        return Display("What?") 
    
    def display_channel(self, message):
        if (message.originator != self):
            self.session.display_line(message.display_line)
    
    def register_channel(self, channel):
        self.registrations.add(self.register(channel, self.display_channel))
    
    def detach(self):
        for registration in self.registrations:
            registration.detach()         
        self.session = None
        
        
            