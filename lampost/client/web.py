from lampost.client.clientdata import NewCharacterData
from lampost.client.handlers import GameConnect, Link, Login, Action, Register, Unregister, RemoteLog
from lampost.client.messages import FriendResponse, MessageDelete
from lampost.client.settings import Settings
from lampost.context.config import m_configured


m_configured(__name__, 'mud_title', 'mud_description')

_web_server = None


def _on_configured():
    if _web_server:
        _web_server.lsp_js('config.js', "var lampost_config = {{title:'{0}', description:'{1}'}};".format(mud_title, mud_description))


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

    web_server.add(r'/client_data/new_char', NewCharacterData)

    web_server.add(r'/messages/friend_response', FriendResponse)
    web_server.add(r'/messages/delete', MessageDelete)

    web_server.add(r'/settings/(.*)', Settings)

    _on_configured()
