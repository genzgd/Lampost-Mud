'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action, SayAction
from avezel import Avezel
from channel import Channel
from emote import Emotes
from entity import Soul
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
        new_soul = MudSoul()
        new_soul.actions.add(self.shout_channel)
        new_soul.targets.add(self.shout_channel)
        
        create_player = CreatePlayer()
        delete_player = DeletePlayer()
        new_soul.actions.add(create_player)
        new_soul.targets.add(create_player)
        new_soul.actions.add(delete_player)
        new_soul.targets.add(delete_player)
        
        player.baptise(new_soul, set(), self.area.rooms[0])
        player.register_channel(self.shout_channel)
        player.register("db_log", player.display_line)
        

class MudSoul(Soul):
    look_action = Action(("look", "l", "exa", "examine"), CLASS_SENSE_EXAMINE)
    say_action = SayAction()
    emotes = Emotes()
    def __init__(self):
        Soul.__init__(self)
        self.actions.update((MudSoul.look_action, MudSoul.say_action, MudSoul.emotes))
        self.actions.update(Directions().actions)
      
