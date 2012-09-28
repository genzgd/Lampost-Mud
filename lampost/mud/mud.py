import lampost.immortal.immortal
import lampost.comm.chat
import lampost.action.inventory
import lampost.action.emote

from lampost.action.action import simple_action
from lampost.mud.action import mud_actions, imm_actions
from lampost.context.resource import provides, requires, m_requires
from lampost.immortal.citadel import ImmortalCitadel
from lampost.comm.channel import Channel

from area import Area

from lampost.merc.flavor import MercFlavor
from lampost.mobile.mobile import MobileTemplate, Mobile
from lampost.player.player import Player
from lampost.model.article import Article, ArticleTemplate

m_requires('log', 'perm', __name__)

@requires('sm', 'datastore')
@provides('nature')
class MudNature():

    def __init__(self):
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        look_action = simple_action(("look", "l", "exa", "examine", "look at"), "examine")
        self.basic_soul = {look_action}
        for action in mud_actions:
            self.basic_soul.add(action)
        self.mud = Mud()
        self.citadel = ImmortalCitadel()
        self.mud.add_area(self.citadel)
        self.citadel.on_loaded()
        self.basic_soul.add(self.shout_channel)

    def editors(self, player):
        editors = []
        if has_perm(player, 'supreme'):
            editors.append('config')

        if has_perm(player, 'admin'):
            editors.append('areas')
            editors.append('players')

        return editors

    def baptise(self, player):
        if not getattr(player, "flavor", None):
            self.mud.init_player(player)
            self.datastore.save_object(player)

        new_soul = self.basic_soul.copy()

        if player.imm_level:
            new_soul.add(self.imm_channel)
            player.register_channel(self.imm_channel)
            player.build_mode = True
            for cmd in imm_actions:
                if player.imm_level >= perm_level(cmd.imm_level):
                    new_soul.add(cmd)

        player.baptise(new_soul)
        player.register_channel(self.shout_channel)

        if has_perm(player, 'supreme'):
            player.register("db_log", player.display_line)
            player.register("debug", player.display_line)
            player.register("error", player.display_line)

        player.equip(set())
        self.mud.enhance_player(player)
        self.mud.start_player(player)

@requires('datastore', 'dispatcher', 'config')
@provides('mud')
class Mud():
    def __init__(self):
        MobileTemplate.mud = self
        self.flavor = MercFlavor()
        self.flavor.apply_mobile(Mobile)
        self.flavor.apply_mobile_template(MobileTemplate)
        self.flavor.apply_player(Player)
        self.flavor.apply_article(Article)
        self.flavor.apply_article_template(ArticleTemplate)

        self.area_map = {}
        area_keys = self.datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = area_key.split(":")[1]
            area = self.datastore.load_object(Area, area_id)
            self.add_area(area)

    def add_area(self, area):
        self.area_map[area.dbo_id] = area

    def get_area(self, area_id):
        return self.area_map.get(area_id)

    def init_player(self, player):
        player.flavor = self.flavor.flavor
        player.room_id = self.config.start_room
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
                error("Unable to find room for " + room_id)
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
