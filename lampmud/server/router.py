from lampost.server.handlers import Action, RemoteLog
from lampost.server.settings import Settings

from lampmud.server.messages import FriendResponse, MessageDelete

routes = [
    ('action', Action),
    ('messages/friend_response', FriendResponse),
    ('messages/delete', MessageDelete),
    ('settings/(.*)', Settings)
]
