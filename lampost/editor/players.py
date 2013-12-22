from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.model.player import Player
from lampost.client.user import User

m_requires('datastore', 'perm', 'user_manager', __name__)


class PlayerResource(EditResource):
    def pre_delete(self, player, session):
        if player.imm_level >= perm_level('supreme'):
            raise DataError("Cannot delete root user.")
        if hasattr(player, 'session'):
            raise DataError("Player is logged in.")
        check_player_perm(player, session)

    def post_delete(self, player, session):
        user = load_object(User, player.user_id)
        user_manager.delete_player(user, player.dbo_id)
        if not user.player_ids:
            user_manager.delete_user(user)


def check_player_perm(player, session):
    user = load_object(User, player.user_id)
    if user_manager.user_imm_level(user) > 0:
        check_perm(session, 'supreme')
    else:
        check_perm(session, 'admin')
