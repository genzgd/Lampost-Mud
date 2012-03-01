'''
Created on Feb 15, 2012

@author: Geoff
'''
from action import Action
from dto.display import DisplayLine, Display
from responder import Responder

from message import LMessage

class Channel(Action, Responder):
    def __init__(self, verb, color=0x000000):
        Action.__init__(self, verb, self)
        self.color = color
    
    def create_message(self, source, verb, subject, command):
        if subject:
            return LMessage(source, self.msg_class, source.name + ": " + command[command.find(" "):])
             
    def receive(self, lmessage):
        self.dispatch(self, ChannelMessage(lmessage.source, lmessage.payload, self.color));
        return Display(lmessage.payload, self.color)
        
class ChannelMessage():
    def __init__(self, source, message, color):
        self.source = source
        self.display_line = DisplayLine(message, color)  
    