from lampost.di.resource import Injected, module_inject
from lampost.server.handlers import SessionHandler

um = Injected('user_manager')
friend_service = Injected('friend_service')
message_service = Injected('message_service')
module_inject(__name__)


class FriendResponse(SessionHandler):

    def main(self):
        source_id = self.raw['source_id']
        player_id = self.raw['player_id']
        friend_service.remove_request(source_id, player_id)
        message_service.remove_message(player_id, self.raw['msg_id'])
        if self.raw['action'] == 'accept':
            friend_service.add_friend(source_id, player_id)
            message_service.add_message("system", "{} has accepted your friend request.".format(um.id_to_name(player_id)), source_id)
            message_service.add_message("system", "You have accepted {}'s friend request.".format(um.id_to_name(source_id)), player_id)
        elif self.raw['action'] == 'block':
            message_service.block_messages(player_id, source_id)
        else:
            message_service.add_message("system", "{} has declined your friend request.".format(um.id_to_name(player_id)), source_id)
            message_service.add_message("system", "You have declined {}'s friend request.".format(um.id_to_name(source_id)), player_id)


class MessageDelete(SessionHandler):

    def main(self):
        message_service.remove_message(**self.raw)





