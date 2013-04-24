from lampost.context.resource import m_requires
from lampost.model.player import Player
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_displays

m_requires('log', 'config_manager', 'perm', 'datastore', __name__)


def displays():
    config_manager.config.default_displays = build_default_displays()
    config_manager.save_config()


def player_race():
    for player_id in fetch_set_keys(Player.dbo_set_key):
        player = load_object(Player, player_id)
        if getattr(player, 'race', None) != 'mutt':
            continue
        player.race = 'mutt'
        for attr in PlayerRace.attr_list:
            setattr(player, attr, PlayerRace.base_attr_value)
            setattr(player, '{}_perm'.format(attr), PlayerRace.base_attr_value)
        save_object(player)









