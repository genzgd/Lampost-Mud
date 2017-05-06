from lampost.di.app import on_app_start
from lampost.server.link import LinkListener
from lampost.di.resource import Injected, module_inject

db = Injected('datastore')
module_inject(__name__)


@on_app_start
def _start():
    LinkListener('new_char_data', _new_char_data)


def _new_char_data(**_):
    return {'races': {race.dbo_id: _race_dto(race) for race in db.load_object_set('race')}}


def _race_dto(race):
    return {'name' : race.name, 'desc': race.desc}
