from lampost.context.resource import m_requires
from lampost.lpflavor.setup import default_skills
from lampost.model.player import Player
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_displays, build_config_settings

m_requires('log', 'config_manager', 'perm', 'datastore', 'skill_service', 'dispatcher', __name__)


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
    build_config_settings(config_manager.config)
    config_manager.save_config()
    return "Configuration updated"









