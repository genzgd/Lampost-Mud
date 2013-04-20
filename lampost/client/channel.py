from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires

m_requires('log', 'channel_service', __name__)

class ChannelResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild("gen_channels", GeneralChannels())


class GeneralChannels(Resource):
    @request
    def render_POST(self, session, content):
        return channel_service.gen_channels()

