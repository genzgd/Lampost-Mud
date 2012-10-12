from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires

m_requires('datastore', 'perm', 'mud',  __name__)

class ConfigResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', ConfigGet())
        self.putChild('update', ConfigUpdate())

@requires('config')
class ConfigGet(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'supreme')
        return self.config.json_obj

@requires('config', 'dispatcher')
class ConfigUpdate(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'supreme')
        update_object(self.config, content.config)
        self.dispatcher.dispatch('config_updated')
        return self.config.json_obj