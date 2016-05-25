from lampmud.lpmud.attributes import fill_pools, base_pools
from lampmud.lpmud.skill import add_skill
from lampmud.context.resource import m_requires

m_requires(__name__,  'dispatcher')


def _post_init():
    register('player_create', _player_create, priority=1000)
    register('player_baptise', _player_baptise)
    register('player_connect', _player_connect)


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


def _player_baptise(player):
    if player.race:
        for default_skill in player.race.default_skills:
            if default_skill.skill_template.dbo_key not in player.skills.keys():
                add_skill(default_skill.skill_template, player, default_skill.skill_level, 'race')

    base_pools(player)
    player.start_refresh()


def _player_connect(player, *_):
    player.status_change()
