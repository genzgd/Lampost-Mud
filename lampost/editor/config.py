from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires

m_requires('perm', __name__)


class ConfigResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', ConfigGet())
        self.putChild('update', ConfigUpdate())


@requires('config_manager')
class ConfigGet(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'supreme')
        return self.config_manager.config_json


@requires('config_manager', 'dispatcher')
class ConfigUpdate(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'supreme')
        self.config_manager.update_config(content.config)
        return self.config_manager.config_json