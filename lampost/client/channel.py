from lampost.client.handlers import SessionHandler
from lampost.context.resource import m_requires

m_requires('log', 'channel_service', 'web_server', __name__)


def _post_init():
    web_server.add(r"/channel/(.*)", Channel)


class Channel(SessionHandler):
    def main(self, channel_name):
        return getattr(channel_service, channel_name)()

