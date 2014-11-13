from lampost.client.handlers import MethodHandler
from lampost.context.resource import m_requires

m_requires(__name__, 'channel_service')


class Channel(MethodHandler):
    def gen_channels(self):
        return channel_service.gen_channels()
