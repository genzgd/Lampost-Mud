import sys
from lampost.env.room import Exit
from lampost.lpflavor import setup
from lampost.lpflavor.attributes import ATTR_LIST, ATTR_MAP, fill_pools, base_pools
from lampost.lpflavor.combat import DAMAGE_TYPES, DAMAGE_DELIVERY
from lampost.lpflavor.env import ExitLP
from lampost.lpflavor.mobile import MobileLP
from lampost.lpflavor.skill import SkillService
from lampost.model.mobile import Mobile
from lampost.model.player import Player
from lampost.lpflavor.player import PlayerLP

from lampost.context.resource import m_requires
from lampost.model.race import PlayerRace

m_requires('cls_registry', 'context', 'dispatcher', 'datastore', 'perm', __name__)

equip_slots = ['none', 'finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']

SkillService()


def _post_init():
    PlayerRace.attr_list = ATTR_LIST

    cls_registry.set_class(Player, PlayerLP)
    cls_registry.set_class(Mobile, MobileLP)
    cls_registry.set_class(Exit, ExitLP)

    context.set('equip_slots', equip_slots)
    context.set('equip_types', equip_types)
    context.set('attr_map', ATTR_MAP)
    context.set('damage_types', DAMAGE_TYPES)
    context.set('damage_delivery', list(DAMAGE_DELIVERY))

    calc_map = {key: value['name'] for key, value in ATTR_MAP.iteritems()}
    calc_map.update({'roll': "Dice roll adjust (20 sided)",
                     'skill': "Skill level adjust"})
    context.set('calc_map', calc_map)

    register('first_time_setup', setup.first_time_setup)
    register('player_create', _player_create)
    register('player_baptise', _player_baptise)
    register('player_connect', _player_connect)
    register('game_settings', _game_settings)


def _player_create(player):
    race = load_object(PlayerRace, player.race)
    for attr_name, start_value in race.base_attrs.iteritems():
        setattr(player, attr_name, start_value)
        setattr(player, 'perm_{}'.format(attr_name), start_value)
    fill_pools(player)


def _player_baptise(player):
    base_pools(player)
    player.start_refresh()


def _game_settings(game_settings):
    env_module = sys.modules['lampost.lpflavor.env']
    env_module.stamina_calc = game_settings['room_stamina']
    env_module.action_calc = game_settings['room_action']

def _player_connect(player, *ignored):
    player.status_change()







