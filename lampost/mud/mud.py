from importlib import import_module
from lampost.env.movement import Direction
from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.env.room import Room, safe_room
from lampost.gameops.config import m_configured
from lampost.mud.action import imm_actions
from lampost.context.resource import requires, m_requires, register_module
from lampost.comm.channel import Channel

import_module('lampost.model.area')
import_module('lampost.mud.immortal')
import_module('lampost.comm.chat')
import_module('lampost.mud.inventory')
import_module('lampost.mud.socials')
import_module('lampost.mud.group')
import_module('lampost.env.instance')

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'mud_actions', 'perm')

m_configured(__name__, 'default_start_room')

@requires('context', 'instance_manager')
class MudNature():

    def __init__(self, flavor):
        flavor_module = __import__('lampost.' + flavor + '.flavor', globals(), locals())
        register_module(self)

    def _post_init(self):
        self.shout_channel = Channel("shout", general=True)
        self.imm_channel = Channel("imm")

        self.context.set('article_load_types', ['equip', 'default'])
        self.context.set('broadcast_types', broadcast_types)
        self.context.set('broadcast_tokens', broadcast_tokens)
        self.context.set('directions', Direction.ordered)

        register('player_create', self._player_create)
        register('player_baptise', self._baptise, priority=-100)
        register('imm_baptise', self._imm_baptise, priority=-100)
        register('missing_env', self._start_env)

    def _player_create(self, player, user):
        if len(user.player_ids) == 1 and not player.Imm_level:
            player.imm_level = perm_level('builder')
            update_immortal_list(player)
            dispatch('imm_level_change', player, 0)
            message_service.add_message('system', "Welcome!  Your first player has been given builder powers.  Check out the 'Editor' window on the top menu.", player.dbo_id)
        player.room_id = default_start_room

    def _baptise(self, player):
        player.baptise()
        self.shout_channel.add_sub(player)
        if player.imm_level:
            dispatch("imm_baptise", player)
        player.change_env(self._start_env(player))

    def _imm_baptise(self, player):
        player.can_die = False
        player.immortal = True
        self.imm_channel.add_sub(player)
        for cmd in imm_actions:
            if player.imm_level >= perm_level(cmd.imm_level):
                player.enhance_soul(cmd)
            else:
                player.diminish_soul(cmd)

    def _start_env(self, player):
        instance = self.instance_manager.get(player.instance_id)
        instance_room = load_object(player.instance_room_id, Room, silent=True)
        player_room = load_object(player.room_id, Room, silent=True)

        if instance and instance_room:
            # Player is returning to an instance still in memory
            return instance.get_room(player.instance_room_id)

        if instance_room and not player_room:
            # Player has no 'non-instanced' room, so presumably was created in a new instanced tutorial/racial area
            instance = self.instance_manager.next_instance()
            return instance.get_room(player.instance_room_id)

        # If we get here whatever instance data was associated with the player is no longer valid
        del player.instance_id
        del player.instance_room_id

        if player_room:
            return player_room

        default_start = load_object(default_start_room, Room)
        if default_start:
            return default_start

        # This really should never happen
        error("Unable to find valid room for player login", stack_info=True)
        del player.room_id
        save_object(player)
        return safe_room
