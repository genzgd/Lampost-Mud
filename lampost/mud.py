'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action, SayAction, TARGET_GENERAL
from avezel import Avezel
from channel import Channel
from emote import Emotes
from immortal import CreatePlayer, DeletePlayer
from message import CLASS_SENSE_EXAMINE
from movement import Directions


class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        
    def create(self):
        self.area = Avezel()

    def baptise(self, player):
        new_soul = MudSoul.mud_soul
        new_soul.add(self.shout_channel)
        
        new_soul.add(CreatePlayer())
        new_soul.add(DeletePlayer())
        
        player.baptise(new_soul, set(), self.area.rooms[0])
        player.register_channel(self.shout_channel)
        player.register("db_log", player.display_line)
        

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine"), CLASS_SENSE_EXAMINE, TARGET_GENERAL)
    say_action = SayAction()
    emotes = Emotes()
    mud_soul = set((look_action, say_action, emotes)) | Directions.actions