from lampost.client.resources import SessionHandler
from lampost.context.resource import m_requires

m_requires('log', 'channel_service', __name__)


class ChannelResource(SessionHandler):

    def main(self, channel_name):
        return getattr(channel_service, channel_name)()

