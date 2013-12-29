from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.gameops.template import template_class
from lampost.model.article import ArticleTemplate, Article
from lampost.model.entity import enhance_soul, diminish_soul
from lampost.model.mobile import MobileTemplate, Mobile
from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.mud.action import imm_actions, MudActions
from lampost.context.resource import provides, requires, m_requires
from lampost.comm.channel import Channel

from lampost.model.area import Area

__import__('lampost.mud.immortal')
__import__('lampost.comm.chat')
__import__('lampost.mud.inventory')
__import__('lampost.mud.socials')

m_requires('log', 'datastore', 'dispatcher', 'perm', __name__)


@requires('context', 'config_manager')
@provides('nature')
class MudNature():

    def __init__(self, flavor):
        flavor_module = __import__('lampost.' + flavor + '.flavor', globals(), locals())
        MudActions()

    def _post_init(self):
        self.shout_channel = Channel("shout")
        self.imm_channel = Channel("imm")

        self.context.set('article_load_types', ['equip', 'default'])
        self.context.set('broadcast_types', broadcast_types)
        self.context.set('broadcast_tokens', broadcast_tokens)
        self.context.set('directions', Direction.ordered)

        template_class(ArticleTemplate, Article)
        template_class(MobileTemplate, Mobile)

        register('game_settings', self._game_settings)
        register('player_connect', self._player_connect)
        register('player_baptise', self._baptise, priority=-100)
        register('imm_baptise', self._imm_baptise, priority=-100)

    def start_service(self):
        info("Loading mud", self)
        load_object_set(Area)
        info("Mud loaded", self)

    def _imm_baptise(self, player):
        player.build_mode = True
        player.register_channel(self.imm_channel)
        for cmd in imm_actions:
            if player.imm_level >= perm_level(cmd.imm_level):
                enhance_soul(player, cmd)
            else:
                diminish_soul(player, cmd)

    def _game_settings(self, game_settings):
        Area.reset_time = game_settings.get('area_reset', 180)
        Room.size = game_settings.get('room_size', 10)

    def _player_connect(self, player, client_data):
        editors = []
        channels = ['shout_channel']
        if has_perm(player, 'creator'):
            editors.append('area')
            editors.append('room')
            editors.append('mobile')
            editors.append('article')
            channels.append('imm_channel')
        if has_perm(player, 'admin'):
            editors.append('players')
            editors.append('social')
            editors.append('display')
            editors.append('race')
            editors.append('attack')
            editors.append('defense')
        if has_perm(player, 'supreme'):
            editors.append('config')

        client_data['editors'] = editors
        client_data['avail_channels'] = channels
        client_data['active_channels'] = player.active_channels
        player.parse('look')

    def _baptise(self, player):
        player.baptise()
        if player.imm_level:
            dispatch("imm_baptise", player)
        player.register_channel(self.shout_channel)

        if has_perm(player, 'supreme'):
            register("log", player.display_line)

        player.equip(set())
        if hasattr(player, "room_id"):
            room = load_object(Room, player.room_id)
        else:
            room = load_object(Room, self.config_manager.start_room)
            if room:
                player.room_id = player.env.dbo_id
                save_object(player)
        if not room:
            room = Room("temp_start_room", "A Temporary Room when Start Room is Missing")
        player.change_env(room)
