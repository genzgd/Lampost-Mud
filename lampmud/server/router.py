from lampost.server.handlers import GameConnect, Link, Login, Action, Register, Unregister, RemoteLog
from lampost.server.settings import Settings

from lampmud.server.messages import FriendResponse, MessageDelete

routes = [
    ('game_connect', GameConnect),
    ('link', Link),
    ('login', Login),
    ('action', Action),
    ('register', Register),
    ('unregister', Unregister),
    ('remote_log', RemoteLog),
    ('messages/friend_response', FriendResponse),
    ('messages/delete', MessageDelete),
    ('settings/(.*)', Settings)
]
