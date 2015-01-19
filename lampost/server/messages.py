from lampost.context.resource import m_requires
from lampost.server.handlers import SessionHandler

m_requires(__name__, 'log', 'friend_service', 'message_service', 'user_manager')


class FriendResponse(SessionHandler):

    def main(self):
        source_id = self.raw['source_id']
        player_id = self.raw['player_id']
        friend_service.remove_request(source_id, player_id)
        message_service.remove_message(player_id, self.raw['msg_id'])
        if self.raw['action'] == 'accept':
            friend_service.add_friend(source_id, player_id)
            message_service.add_message("system", "{} has accepted your friend request.".format(user_manager.id_to_name(player_id)), source_id)
            message_service.add_message("system", "You have accepted {}'s friend request.".format(user_manager.id_to_name(source_id)), player_id)
        elif self.raw['action'] == 'block':
            message_service.block_messages(player_id, source_id)
        else:
            message_service.add_message("system", "{} has declined your friend request.".format(user_manager.id_to_name(player_id)), source_id)
            message_service.add_message("system", "You have declined {}'s friend request.".format(user_manager.id_to_name(source_id)), player_id)


class MessageDelete(SessionHandler):

    def main(self):
        message_service.remove_message(**self.raw)





