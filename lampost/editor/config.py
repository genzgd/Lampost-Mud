from twisted.web.resource import Resource
from lampost.client.handlers import request
from lampost.context.resource import m_requires

m_requires('perm', 'datastore', 'config_manager', __name__)


class ConfigResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', ConfigGet())
        self.putChild('get_defaults', ConfigDefaults())
        self.putChild('update', ConfigUpdate())


class ConfigGet(Resource):
    @request
    def render_POST(self, session):
        check_perm(session, 'supreme')
        return config_manager.config_json


class ConfigUpdate(Resource):
    @request
    def render_POST(self, raw, session):
        check_perm(session, 'supreme')
        config_manager.update_config(raw)
        return config_manager.config_json


class ConfigDefaults(Resource):
    @request
    def render_POST(self, session):
        check_perm(session, 'supreme')
        return {'server': load_raw('server_settings_default'), 'game': load_raw('game_settings_default')}
