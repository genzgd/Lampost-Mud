from lampost.context.resource import m_requires, provides

m_requires('datastore', 'dispatcher', __name__)

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

    def is_friend(self, player, friend_id):
        return set_key_exists('friends:{}'.format(player.dbo_id), friend_id)

    def check_friends(self, player):
        pass


