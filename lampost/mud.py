'''
Created on Feb 25, 2012

@author: Geoff
'''
from action import Action
from citadel import ImmortalCitadel
from channel import Channel
from emote import Emotes
from immortal import CreatePlayer, DeletePlayer, CreateArea,\
    GoToArea, Citadel, RegisterDisplay, UnregisterDisplay, IMM_LEVELS, Describe,\
    ListCommands, AreaList, GotoRoom, SetHome, GoHome, Zap, PatchDB, PatchTarget
from area import Area
from chat import TellAction, ReplyAction, SayAction
from builder import Dig, RoomList, UnDig, SetDesc, SetTitle, BackFill, BuildMode,\
    FTH, DelRoom, MobList, ResetRoom, CreateMob, AddMob, DelMob, EditAreaMob,\
    DeleteArea
from lampost.merc.flavor import MercFlavor
from mobile import MobileTemplate, Mobile
from player import Player

IMM_COMMANDS = CreatePlayer(), DeletePlayer(), CreateArea(), DeleteArea(), GoToArea(), Citadel(),\
    RegisterDisplay(), UnregisterDisplay(), Describe(), Dig(), RoomList(), ListCommands(),\
    AreaList(), GotoRoom(), UnDig(), SetHome(), GoHome(), SetDesc(), SetTitle(), BackFill(),\
    BuildMode(), FTH(), DelRoom(), MobList(), Zap(), ResetRoom(), CreateMob(), AddMob(), EditAreaMob(), \
    DelMob(), DeleteArea, PatchTarget(), PatchDB()

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        self.basic_soul = MudSoul.mud_soul.copy()
        
    def create(self, datastore):
        self.mud = Mud(datastore, self.dispatcher)
        MobileTemplate.mud = self.mud
        Action.mud = self.mud
        self.citadel = ImmortalCitadel()
        self.mud.add_area(self.citadel)
        self.citadel.on_loaded()
        self.basic_soul.add(self.shout_channel)
       
        
    def baptise(self, player):
        
        if not getattr(player, "mudflavor", None):
            self.mud.init_player(player)
        
        new_soul = self.basic_soul.copy()
       
        for cmd in IMM_COMMANDS:
            if player.imm_level >= cmd.imm_level:
                new_soul.add(cmd)
                
        if player.imm_level:
            new_soul.add(self.imm_channel)
          
        player.baptise(new_soul)
        player.register_channel(self.shout_channel)
        
        if player.imm_level:
            player.register_channel(self.imm_channel)
            
        if player.imm_level == IMM_LEVELS["supreme"]:
            player.register("db_log", player.display_line)
            player.register("debug", player.display_line)
            
        player.equip(set())
        self.mud.enhance_player(player)

        player.enter_env(self.citadel.first_room)
       

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine", "look at"), "examine")
    mud_soul = set((look_action, SayAction(), Emotes(), TellAction(), ReplyAction())) 
    

class Mud():
    def __init__(self, datastore, dispatcher):
        Area.dispatcher = dispatcher
        self.area_map = {}
        self.flavor = MercFlavor()
        area_keys = datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = area_key.split(":")[1]
            area = datastore.load_object(Area, area_id)
            self.add_area(area)
        self.flavor.apply_mobile(Mobile)
        self.flavor.apply_mobile_template(MobileTemplate)
        self.flavor.apply_player(Player)
    
    def add_area(self, area):
        self.area_map[area.dbo_id] = area
        
    def get_area(self, area_id):
        area_id = area_id.lower().split(" ")
        area_id = "_".join(area_id)
        return self.area_map.get(area_id)
    
    def init_player(self, player):
        player.flavor = self.flavor.flavor
        self.flavor.init_player(player)
        
    def enhance_player(self, player):
        self.flavor.enhance_player(player)
        
    def init_mobile(self, mobile):
        self.flavor.init_mobile(mobile)
        