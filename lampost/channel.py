'''
Created on Feb 15, 2012

@author: Geoff
'''
from action import Action
from dto.display import DisplayLine, Display
from responder import Responder

import message

class Channel(Action, Responder):
    def __init__(self, verb, color=0x000000):
        Action.__init__(self, verb, message.CLASS_OUT_OF_CHAR)
        self.color = color
    
    def create_message(self, player, verb, subject):
        return player.name + ": " + " ".join(subject)
    
    def accepts(self, action, subject):
        return action == self and subject
         
    def receive(self, originator, message):
        self.dispatch(self, ChannelMessage(originator, message, self.color));
        return Display(message, self.color)
        
class ChannelMessage():
    def __init__(self, originator, message, color):
        self.originator = originator
        self.display_line = DisplayLine(message, color)  
    