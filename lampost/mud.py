'''
Created on Feb 25, 2012

@author: Geoff
'''
from channel import Channel
from action import Action, SayAction
from avezel import Avezel
from entity import Soul

from message import CLASS_SENSE_EXAMINE
from dto.display import Display
from movement import Directions
from immortal import CreatePlayer
from emote import Emotes

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
        new_soul.actions.add(create_player)
        new_soul.targets.add(create_player)
        
        player.baptise(new_soul, set(), self.area.rooms[0])
        player.register_channel(self.shout_channel)
        player.register("db_log", player.display_line)
  
        welcome = Display("Welcome " + player.name,  0x002288)
        welcome.merge(player.parse("look"))
        return welcome
        

class MudSoul(Soul):
    look_action = Action(("look", "l"), CLASS_SENSE_EXAMINE)
    say_action = SayAction()
    emotes = Emotes()
    def __init__(self):
        Soul.__init__(self)
        self.actions.update((MudSoul.look_action, MudSoul.say_action, MudSoul.emotes))
        self.actions.update(Directions().actions)
      
                                      
         

