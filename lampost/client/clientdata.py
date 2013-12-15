from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.model.race import PlayerRace

m_requires('log', 'datastore', __name__)


class ClientDataResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('new_char', NewCharacterData())


class NewCharacterData(Resource):
    @request
    def render_POST(self, content, session):
        char_data = {'races': {race.dbo_id: race.dto_value for race in load_object_set(PlayerRace)}}
        return char_data


def _race_dto(race):
    return {'name' : race.name, 'desc': race.desc}
