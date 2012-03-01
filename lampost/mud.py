'''
Created on Feb 25, 2012

@author: Geoff
'''
from channel import Channel
from action import Action
from avezel import Avezel
from responder import Responder
from entity import Soul

import message

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("say", 0x109010)
        self.emotes = Emotes()
        self.emotes.channel = self.shout_channel
        self.pulse_interval = .25
        self.basic_soul = Soul()
        self.basic_soul.actions.update((self.emotes, self.shout_channel))
        self.basic_soul.targets.update((self.emotes, self.shout_channel))

    def create(self):
        self.area = Avezel()

    def baptise(self, player):
        player.baptise(self.basic_soul, set(), self.area.rooms[0])
        player.register_channel(self.shout_channel)
                                        
class Emotes(Action, Responder):
    def __init__(self):
        self.verbMap = {"dance": "gyrates obscenely!",
                        "blink": "blinks rapidly in surprise."}
        Action.__init__(self, self.verbMap.keys(), message.CLASS_COMM_GENERAL)
        
    def accepts(self, action, subject):
        return action == self and not subject   
     
    def create_message(self, originator, verb, subject):
        return originator.name + " " + self.verbMap[verb[0]]
        
    def receive(self, originator, message):
        return self.channel.receive(originator, message);
    

