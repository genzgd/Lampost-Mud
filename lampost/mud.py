'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action, SayAction, TARGET_GENERAL
from citadel import ImmortalCitadel
from channel import Channel
from emote import Emotes
from immortal import CreatePlayer, DeletePlayer, CreateArea, DeleteArea,\
    GoToArea, Citadel, RegisterDisplay, UnregisterDisplay
from message import CLASS_SENSE_EXAMINE
from movement import Directions
from area import Area
from chat import TellAction

IMM_COMMANDS = CreatePlayer(), DeletePlayer(), CreateArea(), DeleteArea(), GoToArea(), Citadel(),\
    RegisterDisplay(), UnregisterDisplay()

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        
    def create(self, datastore):
        self.mud = Mud(datastore)
        Action.mud = self.mud
        self.citadel = ImmortalCitadel()
        self.mud.add_area(self.citadel)
        
    def baptise(self, player):
        new_soul = MudSoul.mud_soul
        new_soul.add(self.shout_channel)
        new_soul.add(TellAction())
        
        for cmd in IMM_COMMANDS:
            if player.imm_level >= cmd.imm_level:
                new_soul.add(cmd)
                
        if player.imm_level:
            new_soul.add(self.imm_channel)
          
        player.baptise(new_soul, set(), self.citadel.rooms[0])
        
        if player.imm_level:
            player.register_channel(self.shout_channel)
            player.register_channel(self.imm_channel)  

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine", "look at"), CLASS_SENSE_EXAMINE, TARGET_GENERAL)
    say_action = SayAction()
    emotes = Emotes()
    mud_soul = set((look_action, say_action, emotes)) | Directions.actions
    

class Mud():
    def __init__(self, datastore):
        self.area_map = {}
        area_keys = datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = area_key.split(":")[1]
            area = Area(area_id)
            datastore.hydrate_object(area)
            self.add_area(area)
    
    def add_area(self, area):
        self.area_map[area.dbo_id] = area
        
    def get_area(self, area_id):
        area_id = area_id.lower().split(" ")
        area_id = "_".join(area_id)
        return self.area_map.get(area_id)
        