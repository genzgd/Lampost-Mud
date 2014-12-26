from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.client.user import User
from lampost.editor.editor import Editor
from lampost.model.player import Player
from lampost.util.encrypt import make_hash

m_requires(__name__, 'log', 'datastore', 'perm', 'user_manager', 'edit_update_service')


class PlayerEditor(Editor):
    def initialize(self):
        super().initialize(Player, 'admin')

    def metadata(self):
        return {'perms': {'add': False, 'refresh': True}}

    def _pre_delete(self, player):
        if player.imm_level >= perm_level('supreme'):
            raise DataError("Cannot delete root user.")
        if player.session:
            raise DataError("Player is logged in.")
        check_player_perm(player, self.session)

    def _post_delete(self, player):
        user_manager.remove_player_indexes(player.dbo_id)
        user = load_object(player.user_id, User)
        if not user:
            warn("Removed player without user")
            return
        user.player_ids.remove(player.dbo_id)
        if not user.player_ids:
            delete_object(user)
            publish_edit('delete', user, self.session, True)
        else:
            save_object(user)
            publish_edit('update', user, self.session, True)


def check_player_perm(player, session):
    user = load_object(player.user_id, User)
    if not user:
        error("Missing user for player delete.")
        return
    if user.imm_level > 0:
        check_perm(session, 'supreme')
    else:
        check_perm(session, 'admin')


class UserEditor(Editor):
    def initialize(self):
        super().initialize(User, 'admin')

    def _pre_delete(self, user):
        if user.imm_level:
            raise DataError("Please remove all immortals from this account before deleting.")
        for player_id in user.player_ids:
            player = load_object(player_id, Player)
            if player.session:
                raise DataError("{} is logged in.".format(player.name))

    def _post_delete(self, user):
        for player_id in user.player_ids:
            player = load_object(player_id, Player)
            if player:
                delete_object(player)
                publish_edit('delete', player, self.session, True)

    def _pre_update(self, old_user):
        if self.raw['password']:
            if old_user.dbo_id == self.player.user_id:
                raise DataError("Please change your password through the normal UI.")
            self.raw['password'] = make_hash(self.raw['password'])
            self.raw['password_reset'] = False
        else:
            self.raw['password'] = old_user.password

    def metadata(self):
        return {'perms': {'add': False, 'refresh': True}}
