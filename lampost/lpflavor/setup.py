from lampost.context.resource import m_requires
from lampost.lpflavor.feature.touchstone import Touchstone
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_settings

m_requires(__name__, 'datastore')

GAME_SETTINGS = {'refresh_interval': {'desc': 'Time between entity refreshes (in pulses).',
                                      'default': 12},
                 'room_stamina': {'desc': 'Stamina cost for default room size', 'default': 2},
                 'room_action': {'desc': 'Action cost for default room size', 'default': 10},
                 'stamina_refresh' : {'desc': 'Stamina refresh amount per refresh interval',
                                      'default': 8},
                 'health_refresh': {'desc': 'Health refresh amount per refresh interval', 'default': 1},
                 'mental_refresh': {'desc': 'Mental refresh amount per refresh interval', 'default': 1},
                 'action_refresh': {'desc': 'Action refresh amount per refresh interval', 'default': 40}
                 }


def first_time_setup():
    create_object(PlayerRace, {'dbo_id': 'human', 'name': 'Human'})
    game_settings()


def first_room_setup(room):
    room.features.append(Touchstone())


def game_settings():
    build_default_settings(GAME_SETTINGS, 'game')


