from lampost.context.resource import m_requires
from lampost.datastore.classes import get_dbo_class
from lampost.datastore.exceptions import DataError
from lampost.client.user import User
from lampost.editor.editor import Editor
from lampost.model.player import Player

m_requires(__name__, 'log', 'datastore', 'perm', 'user_manager')


class PlayerEditor(Editor):
    def initialize(self):
        super().initialize(Player)

    def pre_delete(self, player):
        if player.imm_level >= perm_level('supreme'):
            raise DataError("Cannot delete root user.")
        if player.session:
            raise DataError("Player is logged in.")
        check_player_perm(player, self.session)

    def post_delete(self, player):
        user_manager.remove_player_indexes(player.dbo_id)
        user = load_object(player.user_id, User)
        user.player_ids.remove(player.dbo_id)
        if not user.player_ids:
            delete_object(user)
        else:
            save_object(user)

    def metadata(self):
        return {'perms' : {'add': False, 'refresh': True}}


def check_player_perm(player, session):
    user = load_object(player.user_id, User)
    if not user:
        error("Missing user for player delete.")
        return
    if user_manager.user_imm_level(user) > 0:
        check_perm(session, 'supreme')
    else:
        check_perm(session, 'admin')
