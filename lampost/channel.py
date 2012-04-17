'''
Created on Feb 15, 2012

@author: Geoff
'''
from action import Action
from dto.display import DisplayLine, Display


class Channel(Action):
    def __init__(self, verb, color=0x000000):
        Action.__init__(self, verb)
        self.color = color
    
    def execute(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return "Say what?"
        statement = source.name + ":" + command[space_ix:]
        self.dispatch(self, ChannelMessage(source, statement, self.color));
        return Display(statement, self.color)
        
class ChannelMessage():
    def __init__(self, source, message, color):
        self.source = source
        self.display_line = DisplayLine(message, color)  
    