'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action, SayAction, TARGET_GENERAL
from citadel import ImmortalCitadel
from channel import Channel
from emote import Emotes
from immortal import CreatePlayer, DeletePlayer, CreateArea, DeleteArea,\
    IMM_LEVELS
from message import CLASS_SENSE_EXAMINE
from movement import Directions
from area import Area

IMM_COMMANDS = CreatePlayer(), DeletePlayer(), CreateArea(), DeleteArea()

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        
    def create(self, datastore):
        self.mud = Mud(datastore)
        self.citadel = ImmortalCitadel()

    def baptise(self, player):
        new_soul = MudSoul.mud_soul
        new_soul.add(self.shout_channel)
        for cmd in IMM_COMMANDS:
            if player.imm_level >= cmd.imm_level:
                new_soul.add(cmd)
   
        player.baptise(new_soul, set(), self.citadel.rooms[0])
        player.register_channel(self.shout_channel)
        if player.imm_level >= IMM_LEVELS["admin"]:
            player.register("db_log", player.display_line)
        

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine"), CLASS_SENSE_EXAMINE, TARGET_GENERAL)
    say_action = SayAction()
    emotes = Emotes()
    mud_soul = set((look_action, say_action, emotes)) | Directions.actions
    

class Mud():
    def __init__(self, datastore):
        self.area_map = {}
        area_keys = datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = ":".split(area_key)[0]
            self.add_area(Area(area_id))
    
    def add_area(self, area):
        self.area_map[area.dbo_id] = area