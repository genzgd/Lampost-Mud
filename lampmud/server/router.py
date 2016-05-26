from lampost.di.config import m_configured
from lampost.server.handlers import GameConnect, Link, Login, Action, Register, Unregister, RemoteLog
from lampost.server.settings import Settings


from lampmud.server.messages import FriendResponse, MessageDelete

_web_server = None


def _on_configured():
    if _web_server:
        _web_server.lsp_js('config.js', "var lampost_config = {{title:'{0}', description:'{1}'}};".format(lampost_title, lampost_description))


def init(web_server):

    global _web_server
    _web_server = web_server

    web_server.add(r'/game_connect', GameConnect)
    web_server.add(r'/link', Link)
    web_server.add(r'/login', Login)
    web_server.add(r'/action', Action)
    web_server.add(r'/register', Register)
    web_server.add(r'/unregister', Unregister)
    web_server.add(r'/remote_log', RemoteLog)

    web_server.add(r'/messages/friend_response', FriendResponse)
    web_server.add(r'/messages/delete', MessageDelete)

    web_server.add(r'/settings/(.*)', Settings)

    _on_configured()


m_configured(__name__, 'lampost_title', 'lampost_description')
