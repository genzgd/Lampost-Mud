from lampost.context.resource import m_requires, provides

m_requires('datastore', 'dispatcher', 'session_manager', 'perm',  __name__)

@provides('friend_manager')
class FriendManager(object):

    def _post_init(self):
        register('player_login', self.check_friends)

    def add_friend(self, friend_one, friend_two):
        add_set_key('friends:{}'.format(friend_one.dbo_id), friend_two.dbo_id)
        add_set_key('friends:{}'.format(friend_two.dbo_id), friend_one.dbo_id)

    def del_friend(self, friend_one, friend_two):
        del_set_key('friends:{}'.format(friend_one.dbo_id), friend_two.dbo_id)
        del_set_key('friends:{}'.format(friend_two.dbo_id), friend_one.dbo_id)

    def is_friend(self, player, friend):
        return set_key_exists('friends:{}'.format(player.dbo_id), friend.dbo_id)

    def check_friends(self, player):
        email_notifies = fetch_set_keys('email_notifies')
        friend_ids = set()
        email_player_ids = set()
        for immortal_id, perm_level in perm.immortals.iteritems():
            if perm_level >= perm.perm_level('admin') and player.dbo_id != immortal_id:
                friend_ids.add(immortal_id)
        friend_ids.update(fetch_set_keys('friends:{}'.format(player.dbo_id)))
        for friend_id in friend_ids:
            try:
                session_manager.player_session_map[friend_id].append({'friend_login': {'name': player.name}})
            except KeyError:
                if friend_id in email_notifies:
                    email_player_ids.add(friend_id)



