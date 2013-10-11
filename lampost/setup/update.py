from lampost.context.resource import m_requires
from lampost.lpflavor.attributes import POOL_LIST
from lampost.lpflavor.setup import default_skills
from lampost.model.player import Player
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_displays

m_requires('log', 'config_manager', 'perm', 'datastore', 'skill_service', 'dispatcher', __name__)


def displays():
    config_manager.config.default_displays = build_default_displays()
    config_manager.save_config()
    return 'Displays Updated'


def player_race():
    for player_id in fetch_set_keys(Player.dbo_set_key):
        player = load_object(Player, player_id)
        player.race = 'mutt'
        for attr in PlayerRace.attr_list:
            setattr(player, attr, PlayerRace.base_attr_value)
            setattr(player, 'perm_{}'.format(attr), PlayerRace.base_attr_value)
        for pool in POOL_LIST:
            setattr(player, pool, 0)
        save_object(player)
    return 'Players Updated'


def update_skills():
    default_skills()
    detach_events(skill_service)
    skill_service._post_init()
    return 'Default Skills Updated'















