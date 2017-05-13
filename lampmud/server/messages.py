from lampost.di.resource import Injected, module_inject
from lampost.server.link import link_route

um = Injected('user_manager')
friend_service = Injected('friend_service')
message_service = Injected('message_service')
module_inject(__name__)


@link_route('messages/friend_response')
def friend_response(source_id, player_id, action, msg_id, **_):
    friend_service.remove_request(source_id, player_id)
    message_service.remove_message(player_id, msg_id)
    if action == 'accept':
        friend_service.add_friend(source_id, player_id)
        message_service.add_message("system", "{} has accepted your friend request.".format(um.id_to_name(player_id)), source_id)
        message_service.add_message("system", "You have accepted {}'s friend request.".format(um.id_to_name(source_id)), player_id)
    elif action == 'block':
        message_service.block_messages(player_id, source_id)
    else:
        message_service.add_message("system", "{} has declined your friend request.".format(um.id_to_name(player_id)), source_id)
        message_service.add_message("system", "You have declined {}'s friend request.".format(um.id_to_name(source_id)), player_id)


@link_route('messages/delete')
def message_delete(player_id, msg_id, **_):
    message_service.remove_message(player_id, msg_id)





