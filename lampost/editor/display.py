from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires

m_requires('datastore', 'perm', 'config_manager', __name__)


class DisplayResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', DisplayList())
        self.putChild('update', DisplayUpdate())


class DisplayList(Resource):

    @request
    def render_POST(self):
        return config_manager.config.default_displays


class DisplayUpdate(Resource):

    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        config_manager.config.default_displays = content.displays
        config_manager.save_config()
