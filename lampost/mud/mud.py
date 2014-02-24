from importlib import import_module
from lampost.env.movement import Direction
from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.env.room import Room
from lampost.mud.action import imm_actions
from lampost.context.resource import requires, m_requires, register_module
from lampost.comm.channel import Channel


room_module = import_module('lampost.env.room')
__import__('lampost.model.area')
__import__('lampost.mud.immortal')
__import__('lampost.comm.chat')
__import__('lampost.mud.inventory')
__import__('lampost.mud.socials')
__import__('lampost.env.instance')

m_requires('log', 'datastore', 'dispatcher', 'mud_actions', 'perm', __name__)


@requires('context', 'config_manager')
class MudNature():

    def __init__(self, flavor):
        flavor_module = __import__('lampost.' + flavor + '.flavor', globals(), locals())
        register_module(self)

    def _post_init(self):
        self.shout_channel = Channel("shout")
        self.imm_channel = Channel("imm")

        self.context.set('article_load_types', ['equip', 'default'])
        self.context.set('broadcast_types', broadcast_types)
        self.context.set('broadcast_tokens', broadcast_tokens)
        self.context.set('directions', Direction.ordered)

        register('game_settings', self._game_settings)
        register('player_connect', self._player_connect)
        register('player_baptise', self._baptise, priority=-100)
        register('imm_baptise', self._imm_baptise, priority=-100)

    def _imm_baptise(self, player):
        player.register_channel(self.imm_channel)
        player.can_die = False
        player.immortal = True
        for cmd in imm_actions:
            if player.imm_level >= perm_level(cmd.imm_level):
                player.enhance_soul(cmd)
            else:
                player.diminish_soul(cmd)

    def _game_settings(self, game_settings):
        room_module.default_room_size = game_settings.get('room_size', room_module.default_room_size)
        room_module.room_reset_time = game_settings.get('room_reset_time', room_module.room_reset_time)

    def _player_connect(self, player, client_data):
        editors = []
        channels = ['shout_channel']
        if has_perm(player, 'creator'):
            editors.append('area')
            editors.append('room')
            editors.append('mobile')
            editors.append('article')
            editors.append('script')
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
        client_data['active_channels'] = [channel.id for channel in player.active_channels]

    def _baptise(self, player):
        player.baptise()
        if player.imm_level:
            dispatch("imm_baptise", player)
        player.register_channel(self.shout_channel)

        if has_perm(player, 'supreme'):
            register("log", player.display_line)

        room = None
        if hasattr(player, "room_id"):
            room = load_object(Room, player.room_id)
        if not room:
            room = load_object(Room, self.config_manager.start_room)
            if room:
                player.room_id = room.dbo_id
                save_object(player)
        if not room:
            room = Room('temp:start')
            room.title = "Temp Start Room"
            room.desc = "A Temporary Room when Start Room is Missing"
            try:
                del player.room_id
                save_object(player)
            except AttributeError:
                pass
        player.change_env(room)
