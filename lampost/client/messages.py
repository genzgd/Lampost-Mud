from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires

m_requires('log', 'friend_service', 'message_service', 'user_manager', __name__)


class MessagesResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild("friend_response", FriendResponse())
        self.putChild("delete", MessageDelete())


class FriendResponse(Resource):
    @request
    def render_POST(self, content, session):
        source_id = content.source_id
        player_id = content.player_id
        friend_service.remove_request(source_id, player_id)
        message_service.remove_message(player_id, content.msg_id)
        if content.action == 'accept':
            friend_service.add_friend(source_id, player_id)
            message_service.add_message("system", "{} has accepted your friend request.".format(user_manager.id_to_name(player_id)), source_id)
            message_service.add_message("system", "You have accepted {}'s friend request.".format(user_manager.id_to_name(source_id)), player_id)
        elif content.action == 'block':
            message_service.block_messages(player_id, source_id)
        else:
            message_service.add_message("system", "{} has declined your friend request.".format(user_manager.id_to_name(content.player_id)), source_id)
            message_service.add_message("system", "You have declined {}'s friend request.".format(user_manager.id_to_name(source_id)), player_id)


class MessageDelete(Resource):
    @request
    def render_POST(self, content, session):
        message_service.remove_message(content.player_id, content.msg_id)



