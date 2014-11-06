from lampost.client.handlers import SessionHandler
from lampost.context.resource import m_requires

m_requires('channel_service',  __name__)


class Channel(SessionHandler):
    def main(self, channel_name):
        return getattr(channel_service, channel_name)()

