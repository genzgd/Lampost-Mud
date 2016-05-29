from lampost.server.handlers import GameConnect, Link, Login, Action, Register, Unregister, RemoteLog
from lampost.server.settings import Settings

from lampmud.server.messages import FriendResponse, MessageDelete

routes = [
    (r'/game_connect', GameConnect),
    (r'/link', Link),
    (r'/login', Login),
    (r'/action', Action),
    (r'/register', Register),
    (r'/unregister', Unregister),
    (r'/remote_log', RemoteLog),
    (r'/messages/friend_response', FriendResponse),
    (r'/messages/delete', MessageDelete),
    (r'/settings/(.*)', Settings)
]
