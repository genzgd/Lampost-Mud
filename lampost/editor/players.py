from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.client.user import User

m_requires('log', 'datastore', 'perm', 'user_manager', __name__)


class PlayerResource(EditResource):
    def pre_delete(self, player, session):
        if player.imm_level >= perm_level('supreme'):
            raise DataError("Cannot delete root user.")
        if hasattr(player, 'session'):
            raise DataError("Player is logged in.")
        check_player_perm(player, session)

    def post_delete(self, player, session):
        user_manager.remove_player_indexes(player.dbo_id)
        user = load_object(User, player.user_id)
        user.player_ids.remove(player.dbo_id)
        if not user.player_ids:
            delete_object(user)
        else:
            save_object(user)


def check_player_perm(player, session):
    user = load_object(User, player.user_id)
    if not user:
        error("Missing user for player delete.")
        return
    if user_manager.user_imm_level(user) > 0:
        check_perm(session, 'supreme')
    else:
        check_perm(session, 'admin')
