'''
Created on Feb 15, 2012

@author: Geoff
'''
from action import Action, TARGET_ACTION
from dto.display import DisplayLine, Display

from message import LMessage

class Channel(Action):
    def __init__(self, verb, color=0x000000):
        Action.__init__(self, verb, None, TARGET_ACTION)
        self.color = color
    
    def create_message(self, source, verb, target, command):
        space_ix = command.find(" ")
        if space_ix == -1:
            return LMessage(source, None, "Say what?")
        statement = source.name + ":" + command[space_ix:]
        self.dispatch(self, ChannelMessage(source, statement, self.color));
        return LMessage(source, None, Display(statement, self.color))
        
class ChannelMessage():
    def __init__(self, source, message, color):
        self.source = source
        self.display_line = DisplayLine(message, color)  
    