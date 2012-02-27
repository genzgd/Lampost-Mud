'''
Created on Feb 15, 2012

@author: Geoff
'''
from action import Action
from dto.display import DisplayLine, Display

class Channel(Action):
    def __init__(self, verb, color=0x000000):
        self.verbs = set([verb])
        self.color = color
    
    def invoke(self, player, command):
        message =  player.name + ": " + command[command.find(" "):]
        self.broadcast(player, message)
        return Display(message, self.color)
        
    def broadcast(self, originator, message):
        self.dispatch(self, ChannelMessage(originator, message, self.color));
        
        
class ChannelMessage():
    def __init__(self, originator, message, color):
        self.originator = originator
        self.display_line = DisplayLine(message, color)  
    