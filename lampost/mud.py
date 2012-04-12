'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action, SayAction, TARGET_GENERAL
from citadel import ImmortalCitadel
from channel import Channel
from emote import Emotes
from immortal import CreatePlayer, DeletePlayer, CreateArea, DeleteArea,\
    GoToArea, Citadel, RegisterDisplay, UnregisterDisplay, IMM_LEVELS, Describe,\
    ListCommands, AreaList, GotoRoom
from message import CLASS_SENSE_EXAMINE
from area import Area
from chat import TellAction, ReplyAction
from movement import Direction
from builder import Dig, RoomList, UnDig

IMM_COMMANDS = CreatePlayer(), DeletePlayer(), CreateArea(), DeleteArea(), GoToArea(), Citadel(),\
    RegisterDisplay(), UnregisterDisplay(), Describe(), Dig(), RoomList(), ListCommands(),\
    AreaList(), GotoRoom(), UnDig()

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        self.basic_soul = MudSoul.mud_soul.copy()
        
    def create(self, datastore):
        self.mud = Mud(datastore)
        Action.mud = self.mud
        self.citadel = ImmortalCitadel()
        self.mud.add_area(self.citadel)
        self.basic_soul.add(self.shout_channel)
        
    def baptise(self, player):
        new_soul = self.basic_soul.copy()
       
        for cmd in IMM_COMMANDS:
            if player.imm_level >= cmd.imm_level:
                new_soul.add(cmd)
                
        if player.imm_level:
            new_soul.add(self.imm_channel)
          
        player.baptise(new_soul, set(), self.citadel.rooms[0])
        
        if player.imm_level:
            player.register_channel(self.shout_channel)
            player.register_channel(self.imm_channel)
            
        if player.imm_level == IMM_LEVELS["supreme"]:
            player.register("db_log", player.display_line)  

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine", "look at"), CLASS_SENSE_EXAMINE, TARGET_GENERAL)
    mud_soul = set((look_action, SayAction(), Emotes(), TellAction(), ReplyAction())) | Direction.actions
    

class Mud():
    def __init__(self, datastore):
        self.area_map = {}
        area_keys = datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = area_key.split(":")[1]
            area = datastore.load_object(Area, area_id)
            self.add_area(area)
    
    def add_area(self, area):
        self.area_map[area.dbo_id] = area
        
    def get_area(self, area_id):
        area_id = area_id.lower().split(" ")
        area_id = "_".join(area_id)
        return self.area_map.get(area_id)
        