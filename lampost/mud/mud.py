from lampost.env.room import Room
import lampost.mud.immortal
import lampost.comm.chat
import lampost.mud.inventory

from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.mud.socials import SocialRegistry
from lampost.mud.action import imm_actions, MudActions
from lampost.context.resource import provides, requires, m_requires
from lampost.comm.channel import Channel

from lampost.model.area import Area

m_requires('log', 'datastore', 'dispatcher', 'perm', __name__)


@requires('context')
@provides('nature')
class MudNature():

    def __init__(self, flavor):
        flavor_module = __import__('lampost.' + flavor + '.flavor', globals(), locals())
        self.mud = Mud()
        self.mud_actions = MudActions()
        self.social_registry = SocialRegistry()

    def _post_init(self):
        register('player_connect', self._player_connect)
        register('player_baptise', self._baptise)
        info("Loading mud", self)
        self.shout_channel = Channel("shout")
        self.imm_channel = Channel("imm")
        self.context.set('article_load_types', ['equip', 'default'])
        self.context.set('broadcast_types', broadcast_types)
        self.context.set('broadcast_tokens', broadcast_tokens)
        self.mud.load_areas()
        self.social_registry.load_socials()
        info("Mud loaded", self)

    def baptise_imm(self, player):
        if player.imm_level:
            player.build_mode = True
            player.register_channel(self.imm_channel)
        for cmd in imm_actions:
            if player.imm_level >= perm_level(cmd.imm_level):
                player.enhance_soul(cmd)
            else:
                player.diminish_soul(cmd)

    def _player_connect(self, player, client_data):
        editors = []
        channels = ['shout_channel']
        if has_perm(player, 'supreme'):
            editors.append('config')
        if has_perm(player, 'admin'):
            editors.append('players')
            editors.append('socials')
            editors.append('display')
            editors.append('race')
        if has_perm(player, 'creator'):
            editors.append('areas')
            channels.append('imm_channel')
        client_data['editors'] = editors
        client_data['avail_channels'] = channels
        client_data['active_channels'] = player.active_channels

    def _baptise(self, player):
        player.baptise(set())
        if player.imm_level:
            self.baptise_imm(player)
        player.register_channel(self.shout_channel)

        if has_perm(player, 'supreme'):
            player.register("log", player.display_line)

        player.equip(set())
        self.mud.start_player(player)
        if not getattr(player, "room_id", None):
            player.room_id = player.env.dbo_id
            save_object(player)


@provides('mud')
class Mud():
    def __init__(self):
        self.area_map = {}

    def load_areas(self):
        for area_id in fetch_set_keys("areas"):
            area = load_object(Area, area_id)
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

    def start_player(self, player):
        room = None
        if getattr(player, "room_id", None):
            room = self.find_room(player.room_id)
        if not room:
            room = Room("temp_start_room", "A Temporary Room when Start Room is Missing")
        player.change_env(room)
