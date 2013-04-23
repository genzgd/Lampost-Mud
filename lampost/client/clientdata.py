from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires

m_requires('log', 'datastore', __name__)


class ClientDataResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('new_char', NewCharacterData())


class NewCharacterData(Resource):
    @request
    def render_POST(self, content, session):
        char_data = {'races': [race_dto(load_object(PlayerRace, race_id)) for race_id in fetch_set_keys(PlayerRace.dbo_set_key)]}
        return char_data


def _race_dto(race):
    return {'race_id': race.dbo_id, 'name' : race.name, 'desc': race.desc}