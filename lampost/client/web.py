from lampost.client.clientdata import NewCharacterData
from lampost.client.handlers import GameConnect, Link, Login, Action, Register, Unregister, RemoteLog
from lampost.client.messages import FriendResponse, MessageDelete
from lampost.client.settings import Settings


def add_endpoints(web_server):

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