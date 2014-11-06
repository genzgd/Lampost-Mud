from lampost.client.handlers import SessionHandler
from lampost.context.resource import m_requires
from lampost.model.race import PlayerRace

m_requires('log', 'datastore',  __name__)


class NewCharacterData(SessionHandler):

    def post(self):
        self._return({'races': {race.dbo_id: _race_dto(race) for race in load_object_set(PlayerRace)}})


def _race_dto(race):
    return {'name' : race.name, 'desc': race.desc}
