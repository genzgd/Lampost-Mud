from lampost.context.resource import m_requires
from lampost.lpflavor.setup import default_skills, GAME_SETTINGS
from lampost.model.player import Player
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_displays, build_default_settings
from lampost.setup.settings import GAME_SETTINGS_DEFAULT, SERVER_SETTINGS_DEFAULT

m_requires('log', 'config_manager', 'perm', 'social_registry',
           'datastore', 'skill_service', 'dispatcher', __name__)


def displays():
    config_manager.config.default_displays = build_default_displays()
    config_manager.save_config()
    return 'Displays Updated'


def update_skills():
    default_skills()
    detach_events(skill_service)
    skill_service._post_init()
    return 'Default Skills Updated'


def update_config():
    build_default_settings(SERVER_SETTINGS_DEFAULT, 'server')
    build_default_settings(GAME_SETTINGS_DEFAULT, 'game')
    build_default_settings(GAME_SETTINGS, 'game')
    config_manager._dispatch_update()
    return "Configuration updated"


def fix_socials():
    for db_key in fetch_set_keys('socials'):
        social_key = ''.join(['social:', db_key])
        old_social = load_raw(social_key)
        current_social = social_registry._socials.get(db_key)
        current_social.__init__(**old_social.get('map'))
        db_social = {'b_map': old_social.get('map')}
        save_raw(social_key, db_social)










