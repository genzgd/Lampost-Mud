from lampost.context.resource import m_requires, provides
from lampost.util.lmutil import StateError

m_requires('datastore', 'dispatcher', 'session_manager', 'user_manager', 'perm',  __name__)

_REQUEST_KEY = "friend_requests"


@provides('friend_service')
class FriendService(object):

    def _post_init(self):
        register('player_login', self._check_friends)
        register('player_deleted', self._delete_player)

    def friend_request(self, source, target):
        req_key = ':'.join([source.dbo_id, target.dbo_id])
        if set_key_exists(_REQUEST_KEY, req_key):
            raise StateError("You already have a friend request to {} outstanding.".format(target.name))
        dispatch('player_message', 'friend_req', {'friend_id': source.dbo_id, 'friend_name': source.name}, target.dbo_id, source.dbo_id)
        add_set_key(_REQUEST_KEY, req_key)

    def remove_request(self, source_id, target_id):
        delete_set_key('friend_requests', ':'.join([source_id, target_id]))

    def add_friend(self, source_id, target_id):
        add_set_key(friend_key(source_id), target_id)
        add_set_key(friend_key(target_id), source_id)

    def del_friend(self, friend_one_id, friend_two_id):
        delete_set_key(friend_key(friend_one_id), friend_two_id)
        delete_set_key(friend_key(friend_two_id), friend_one_id)

    def friend_list(self, player_id):
        return ' '.join([user_manager.id_to_name(friend_id) for friend_id in fetch_set_keys(friend_key(player_id))])

    def is_friend(self, player_id, friend_id):
        return set_key_exists(friend_key(player_id), friend_id)

    def _check_friends(self, player):
        email_notifies = fetch_set_keys('email_notifies')
        friend_ids = set()
        email_player_ids = set()
        for immortal_id, perm_level in perm.immortals.iteritems():
            if perm_level >= perm.perm_level('admin') and player.dbo_id != immortal_id:
                friend_ids.add(immortal_id)
        friend_ids.update(fetch_set_keys(friend_key(player.dbo_id)))
        for friend_id in friend_ids:
            try:
                session_manager.player_session_map[friend_id].append({'friend_login': {'name': player.name}})
            except KeyError:
                if friend_id in email_notifies:
                    email_player_ids.add(friend_id)

    def _delete_player(self, player):
        for friend_id in fetch_set_keys(friend_key(player.dbo_id)):
            self.del_friend(player.dbo_id, friend_id)

def friend_key(player_id):
    return 'friends:{}'.format(player_id)



