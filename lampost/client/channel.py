from lampost.client.handlers import MethodHandler
from lampost.context.resource import m_requires

m_requires('channel_service', __name__)


class Channel(MethodHandler):
    def gen_channels(self):
        return channel_service.gen_channels()