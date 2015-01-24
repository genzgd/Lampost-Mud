from lampost.context.resource import m_requires
from lampost.lpmud.feature.touchstone import Touchstone
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_settings

m_requires(__name__, 'datastore')


def first_time_setup():
    create_object(PlayerRace, {'dbo_id': 'human', 'name': 'Human'})
    game_settings()


def first_room_setup(room):
    room.features.append(Touchstone())




