from importlib import import_module

from lampost.datastore.dbofield import DBOField
from lampost.lpmud.archetype import PlayerRaceLP
from lampost.lpmud.attributes import ATTR_LIST, fill_pools, base_pools, RESOURCE_POOLS, ATTRIBUTES
from lampost.lpmud.combat import DAMAGE_TYPES, DAMAGE_DELIVERY, WEAPON_OPTIONS, DEFENSE_DAMAGE_TYPES, WEAPON_TYPES
from lampost.lpmud.skill import add_skill
from lampost.lpmud.player import PlayerLP
from lampost.context.resource import m_requires
from lampost.model.race import PlayerRace


m_requires(__name__, 'context', 'dispatcher', 'datastore', 'perm')

m_configured(__name__, 'default_player_race')

equip_slots = ['finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']

__import__('lampost.lpmud.env')
__import__('lampost.lpmud.mobile')
__import__('lampost.lpmud.article')
__import__('lampost.lpmud.archetype')
__import__('lampost.lpmud.feature', globals(), locals(), ['store', 'touchstone'])


def _post_init():
    PlayerRace.attr_list = ATTR_LIST

    PlayerLP.add_dbo_fields({attr: DBOField(0) for attr in ATTR_LIST})
    PlayerLP.add_dbo_fields({pool['dbo_id']: DBOField(0) for pool in RESOURCE_POOLS})

    context.set('equip_slots', equip_slots)
    context.set('equip_types', equip_types)
    context.set('attributes', ATTRIBUTES)
    context.set('damage_types', DAMAGE_TYPES)
    context.set('defense_damage_types', DEFENSE_DAMAGE_TYPES)
    context.set('damage_delivery', DAMAGE_DELIVERY)
    context.set('resource_pools', RESOURCE_POOLS)
    context.set('weapon_types', WEAPON_TYPES)
    context.set('weapon_options', WEAPON_OPTIONS)

    skill_calculation = ATTRIBUTES[:]
    skill_calculation.extend([{'dbo_id': 'roll', 'name': 'Dice Roll'}, {'dbo_id': 'skill', 'name': 'Skill Level'}])
    context.set('skill_calculation', skill_calculation)

    register('first_time_setup', _first_time_setup)
    register('player_create', _player_create, priority=1000)
    register('player_baptise', _player_baptise)
    register('player_connect', _player_connect)


def _first_time_setup():
    new_race_dto = PlayerRaceLP.new_dto()
    new_race_dto.update(default_player_race)
    create_object(PlayerRace, new_race_dto)


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
