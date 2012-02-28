'''
Created on Feb 25, 2012

@author: Geoff
'''
from channel import Channel
from action import Action
from dto.display import Display
from avezel import Avezel

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("say", 0x109010)
        self.emotes = Emotes(self.shout_channel)
        self.pulse_interval = .25

    def create(self):
        self.area = Avezel()

    def baptise(self, player):
        player.world.add(self.shout_channel)
        player.world.add(self.emotes)
        player.register_channel(self.shout_channel)
  
                                           
class Emotes(Action):
    def __init__(self, channel):
        self.channel = channel
        self.verbMap = {"dance": "gyrates obscenely!",
                        "blink": "blinks rapidly in surprise."}
        self.build_verbs(self.verbMap.keys())
     
    def filter_predicate(self, predicate):
        return len(predicate) 
        
    def invoke(self, player, verb, command):
        message = player.name + " " + self.verbMap[verb[0]]
        self.channel.broadcast(player, message);
        return Display(message, self.channel.color)
        

