from lampmud.lpmud.attributes import fill_pools, base_pools
from lampmud.lpmud.skill import add_skill
from lampost.di.resource import m_requires

m_requires(__name__,  'dispatcher')


def _post_init():
    register('player_create', _player_create, priority=1000)


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

