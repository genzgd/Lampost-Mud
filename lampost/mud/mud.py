import lampost.mud.immortal
import lampost.comm.chat
import lampost.mud.inventory

from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.mud.socials import SocialRegistry
from lampost.mud.action import imm_actions, MudActions
from lampost.context.resource import provides, requires, m_requires
from lampost.comm.channel import Channel

from lampost.model.area import Area

m_requires('log', 'perm',  __name__)

article_load_types = ['equip', 'default']

@requires('sm', 'datastore', 'context', 'config')
@provides('nature')
class MudNature():

    def __init__(self, flavor):
        flavor_module = __import__('lampost.' + flavor + '.flavor', globals(), locals(), ['init'])
        flavor_module.init()
        self.mud = Mud()
        self.mud_actions = MudActions()
        self.social_registry = SocialRegistry()

    def _start_service(self):
        debug("Loading mud", self)
        self.shout_channel = Channel("shout", 0x109010)
        self.imm_channel = Channel("imm", 0xed1c24)
        self.pulse_interval = .25
        self.context.set('article_load_types', article_load_types)
        self.context.set('broadcast_types', broadcast_types)
        self.context.set('broadcast_tokens', broadcast_tokens)
        self.mud_actions.add_action(self.shout_channel)

        self.mud.load_areas()
        self.social_registry.load_socials()
        debug("Mud loaded", self)

    def editors(self, player):
        editors = []
        if has_perm(player, 'supreme'):
            editors.append('config')
        if has_perm(player, 'admin'):
            editors.append('players')
            editors.append('socials')
        if has_perm(player, 'creator'):
            editors.append('areas')
        return editors

    def baptise(self, player):
        player.baptise(set())
        if player.imm_level < self.config.auto_imm_level:
            player.imm_level = self.config.auto_imm_level
        if player.imm_level:
            self.baptise_imm(player)
        player.register_channel(self.shout_channel)

        if has_perm(player, 'supreme'):
             player.register("error", player.display_line)

        player.equip(set())
        self.mud.start_player(player)
        if not getattr(player, "room_id", None):
            player.room_id = player.env.dbo_id
            self.datastore.save_object(player)

    def baptise_imm(self, player):
        player.enhance_soul(self.imm_channel)
        player.register_channel(self.imm_channel)
        player.build_mode = True
        for cmd in imm_actions:
            if player.imm_level >= perm_level(cmd.imm_level):
                player.enhance_soul(cmd)
            else:
                player.diminish_soul(cmd)

@requires('datastore', 'dispatcher', 'config')
@provides('mud')
class Mud():
    def __init__(self):
        self.area_map = {}

    def load_areas(self):
        area_keys = self.datastore.fetch_set_keys("areas")
        for area_key in area_keys:
            area_id = area_key.split(":")[1]
            area = self.datastore.load_object(Area, area_id)
            self.add_area(area)
        for area in self.area_map.itervalues():
            area.start()

    def add_area(self, area):
        self.area_map[area.dbo_id] = area

    def get_area(self, area_id):
        return self.area_map.get(area_id)

    def get_mobile(self, mobile_id):
        area = self.get_area(mobile_id.split(':')[0])
        if area:
            return area.get_mobile(mobile_id)
        error('Requested invalid mobileId: {0}'.format(mobile_id))

    def get_article(self, article_id):
        area = self.get_area(article_id.split(':')[0])
        if area:
            return area.get_article(article_id)
        error('Requested invalid articleId: {0}'.format(article_id))

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

    def start_player(self, player):
        room = None
        if getattr(player, "room_id", None):
            room = self.find_room(player.room_id)
        if not room:
            room = self.find_room(self.config.start_room)
        player.change_env(room)
