'''
Created on Feb 25, 2012

@author: Geoff
'''
from lampost.action.action import Action, HelpAction
from lampost.immortal.citadel import ImmortalCitadel
from lampost.comm.channel import Channel
from lampost.action.emote import Emotes, Socials
from lampost.immortal.immortal import CreatePlayer, DeletePlayer, CreateArea,\
    GoToArea, Citadel, RegisterDisplay, UnregisterDisplay, IMM_LEVELS, Describe,\
    ListCommands, AreaList, GotoRoom, SetHome, GoHome, Zap, PatchDB, PatchTarget, GotoPlayer,\
    AllPlayers
from area import Area
from lampost.comm.chat import TellAction, ReplyAction, SayAction
from lampost.immortal.builder import Dig, RoomList, UnDig, SetDesc, SetTitle, BackFill, BuildMode,\
    FTH, DelRoom, MobList, ResetRoom, CreateMob, AddMob, DelMob, EditAreaMob, EditAlias,\
    DeleteArea, AddExtra, DelExtra, CreateRoom
from lampost.merc.flavor import MercFlavor
from lampost.mobile.mobile import MobileTemplate, Mobile
from lampost.player.player import Player
from lampost.gameops.config import Config
from lampost.util.lmlog import error

IMM_COMMANDS = CreatePlayer(), DeletePlayer(), CreateArea(), DeleteArea(), GoToArea(), Citadel(),\
    RegisterDisplay(), UnregisterDisplay(), Describe(), Dig(), RoomList(), ListCommands(),\
    AreaList(), GotoRoom(), UnDig(), SetHome(), GoHome(), SetDesc(), SetTitle(), BackFill(),\
    BuildMode(), FTH(), DelRoom(), MobList(), Zap(), ResetRoom(), CreateMob(), AddMob(), EditAreaMob(), \
    DelMob(), DeleteArea, PatchTarget(), PatchDB(), AddExtra(), DelExtra(), CreateRoom(), GotoPlayer(),  \
    EditAlias(), AllPlayers()

class MudNature():
    
    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        self.basic_soul = MudSoul.mud_soul.copy()
        
    def create(self, datastore):
        self.mud = Mud(datastore, self.dispatcher)
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
            player.build_mode = True
            
        if player.imm_level == IMM_LEVELS["supreme"]:
            player.register("db_log", player.display_line)
            player.register("debug", player.display_line)
            player.register("error", player.display_line)
            
        player.equip(set())
        self.mud.enhance_player(player)
        self.mud.start_player(player)
       

class MudSoul():
    look_action = Action(("look", "l", "exa", "examine", "look at"), "examine")
    mud_soul = set((look_action, SayAction(), Emotes(), TellAction(), ReplyAction(), HelpAction(), Socials())) 
    

class Mud():
    def __init__(self, datastore, dispatcher):
        MobileTemplate.mud = self
        self.config =  datastore.load_object(Config, "config")
        if not self.config:
            self.config = Config()
            datastore.save_object(self.config)
     
        self.flavor = MercFlavor()
        self.flavor.apply_mobile(Mobile)
        self.flavor.apply_mobile_template(MobileTemplate)
        self.flavor.apply_player(Player)
        
        Area.dispatcher = dispatcher
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
    
    def init_player(self, player):
        player.flavor = self.flavor.flavor
        self.flavor.init_player(player)
        
    def enhance_player(self, player):
        self.flavor.enhance_player(player)
        
    def init_mobile(self, mobile):
        self.flavor.init_mobile(mobile)
        
    def find_room(self, room_id):
        try:
            area_id = room_id.split(":")[0]
            area = self.get_area(area_id)
            if not area:
                error("Unable to find area for " + area_id)  
                return None
            room = area.get_room(room_id)
            if not room:
                error("Unable to room for " + room_id)
                return None
            return room
        except:
            error("Exception finding room " + room_id)
            return None
                
    def start_player(self, player):
        if getattr(player, "room_id", None):
            room = self.find_room(player.room_id)
        else:
            room = None
        if not room:
            room = self.find_room(self.config.start_room)
        if not room:
            room = self.find_room("immortal_citadel:0") #Last chance, if this fails something is really wrong
        player.change_env(room)
        