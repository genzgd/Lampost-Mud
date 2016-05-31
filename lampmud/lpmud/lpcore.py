from lampmud.lpmud.attributes import fill_pools
from lampost.di.resource import Injected, module_inject

ev = Injected('dispatcher')
module_inject(__name__)


def _post_init():
    ev.register('player_create', _player_create, priority=1000)


def _player_create(player, user):
    for attr_name, start_value in player.race.base_attrs.items():
        setattr(player, attr_name, start_value)
        setattr(player, 'perm_{}'.format(attr_name), start_value)
    fill_pools(player)
    if player.race.start_instanced:
        player.instance_room_id = player.race.start_room.dbo_id
        player.room_id = None
    else:
        player.room_id = player.race.start_room.dbo_id

