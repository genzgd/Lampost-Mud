import sys
from lampost.datastore.dbo import DBOField
from lampost.env.room import Exit, Room
from lampost.gameops.template import template_class
from lampost.lpflavor import setup
from lampost.lpflavor.archetype import PLayerRaceLP
from lampost.lpflavor.article import ArticleLP, ArticleTemplateLP
from lampost.lpflavor.attributes import ATTR_LIST, ATTR_MAP, \
    fill_pools, base_pools, POOL_MAP
from lampost.lpflavor.combat import DAMAGE_TYPES, DAMAGE_DELIVERY, WEAPON_OPTIONS, DEFENSE_DAMAGE_TYPES, DefenseTemplate, AttackTemplate, DefenseSkill, AttackSkill, WEAPON_TYPES
from lampost.lpflavor.env import ExitLP
from lampost.lpflavor.mobile import MobileLP, MobileTemplateLP
from lampost.lpflavor.skill import add_skill
from lampost.lpflavor.feature.touchstone import TouchStone
from lampost.model.area import Area
from lampost.model.article import Article, ArticleTemplate
from lampost.model.mobile import Mobile, MobileTemplate
from lampost.model.player import Player
from lampost.lpflavor.player import PlayerLP

from lampost.context.resource import m_requires
from lampost.model.race import PlayerRace

m_requires('cls_registry', 'context', 'dispatcher', 'datastore', 'perm', __name__)

equip_slots = ['none', 'finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']


def _post_init():
    PlayerRace.attr_list = ATTR_LIST

    PlayerLP.add_dbo_fields({attr: DBOField(0) for attr in ATTR_LIST})
    PlayerLP.add_dbo_fields({attr: DBOField(0) for attr in POOL_MAP.viewkeys()})

    cls_registry.set_class(Area, Area)
    cls_registry.set_class(Room, Room)
    cls_registry.set_class(Player, PlayerLP)
    cls_registry.set_class(Mobile, MobileLP)
    cls_registry.set_class(Article, ArticleLP)
    cls_registry.set_class(Exit, ExitLP)
    cls_registry.set_class(PlayerRace, PLayerRaceLP)
    cls_registry.set_class(MobileTemplate, MobileTemplateLP)
    cls_registry.set_class(ArticleTemplate, ArticleTemplateLP)
    cls_registry.set_class('attack', AttackTemplate)
    cls_registry.set_class('defense', DefenseTemplate)
    cls_registry.set_class('touchstone', TouchStone)

    context.set('equip_slots', equip_slots)
    context.set('equip_types', equip_types)
    context.set('attr_map', ATTR_MAP)
    context.set('damage_types', DAMAGE_TYPES)
    context.set('defense_damage_types', DEFENSE_DAMAGE_TYPES)
    context.set('damage_delivery', DAMAGE_DELIVERY)
    context.set('resource_pools', POOL_MAP)
    context.set('weapon_types', WEAPON_TYPES)
    context.set('weapon_options', WEAPON_OPTIONS)

    calc_map = {key: value['name'] for key, value in ATTR_MAP.iteritems()}
    calc_map.update({'roll': "Dice roll adjust (20 sided)",
                     'skill': "Skill level adjust"})
    context.set('calc_map', calc_map)

    register('first_time_setup', setup.first_time_setup)
    register('first_room_setup', setup.first_room_setup)
    register('player_create', _player_create)
    register('player_baptise', _player_baptise)
    register('player_connect', _player_connect)
    register('game_settings', _game_settings)

    template_class(DefenseTemplate, DefenseSkill)
    template_class(AttackTemplate, AttackSkill)


def _player_create(player):
    race = load_object(PlayerRace, player.race)
    for attr_name, start_value in race.base_attrs.iteritems():
        setattr(player, attr_name, start_value)
        setattr(player, 'perm_{}'.format(attr_name), start_value)
    fill_pools(player)


def _player_baptise(player):
    race = load_object(PlayerRace, player.race)
    if race:
        for skill_id, skill_status in race.default_skills.iteritems():
            if not skill_id in player.skills.iterkeys():
                add_skill(skill_id, player, skill_status['skill_level'])

    base_pools(player)
    player.start_refresh()


def _game_settings(game_settings):
    env_module = sys.modules['lampost.lpflavor.env']
    env_module.stamina_calc = game_settings.get('room_stamina', 2)
    env_module.action_calc = game_settings.get('room_action', 10)


def _player_connect(player, *ignored):
    player.status_change()
