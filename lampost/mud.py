'''
Created on Feb 25, 2012

@author: Geoff
'''
from channel import Channel
from action import Action
from avezel import Avezel
from entity import Soul

from message import LMessage, CLASS_SENSE_EXAMINE
from dto.display import Display
from movement import Directions

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("say", 0x109010)
        self.emotes = Emotes(self.shout_channel)
        self.pulse_interval = .25
        self.basic_soul = MudSoul()
        self.basic_soul.actions.update((self.emotes, self.shout_channel))
        self.basic_soul.targets.update((self.shout_channel,))

    def create(self):
        self.area = Avezel()

    def baptise(self, player):
        player.baptise(self.basic_soul, set(), self.area.rooms[0])
        player.register_channel(self.shout_channel)
        welcome = Display("Welcome " + player.name,  0x002288)
        welcome.merge(player.parse("look"))
        return welcome
        

class MudSoul(Soul):
    def __init__(self):
        Soul.__init__(self)
        self.actions.add(Action(("look", "l"), CLASS_SENSE_EXAMINE))
        self.actions.update(Directions().get_actions())

                                      
class Emotes(Action):
    def __init__(self, msg_class):
        self.verbMap = {"dance": "gyrates obscenely!",
                        "blink": "blinks rapidly in surprise."}
        Action.__init__(self, self.verbMap.keys(), msg_class)
             
    def create_message(self, source, verb, subject, command):
        if not subject:
            return LMessage(source, self.msg_class, source.name + " " + self.verbMap[verb[0]])
         

