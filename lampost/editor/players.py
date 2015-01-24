from lampost.server.handlers import SessionHandler
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.server.user import User
from lampost.editor.editor import Editor
from lampost.model.player import Player
from lampost.util.encrypt import make_hash

m_requires(__name__, 'log', 'dispatcher', 'datastore', 'perm', 'user_manager', 'edit_notify_service')


def _post_init():
    register('imm_level_change', imm_level_change)


class EditorImmortal():
    def __init__(self, player):
        self.edit_dto = {'dbo_key_type': 'immortal', 'dbo_id': player.dbo_id, 'imm_level': player.imm_level}

    def can_write(self, *_):
        return False

    def can_read(self, *_):
        return False


def imm_level_change(player, old_level, session=None):
    immortal = EditorImmortal(player)
    if not old_level and player.imm_level:
        update_type = 'create'
    elif old_level and not player_imm_level:
        update_type = 'delete'
    else:
        update_type = 'update'
    publish_edit(update_type, immortal, session)


class ImmortalsList(SessionHandler):
    def main(self):
        self._return([{'dbo_id': key, 'name': key, 'imm_level': value, 'dbo_key_type': 'immortal'} for key, value in
                      perm.immortals.items()])


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
        check_player_perm(player, self.player)

    def _post_delete(self, player):
        user_manager.player_cleanup(player.dbo_id)
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

    def _pre_update(self, old_player):
        if self.raw['imm_level'] != old_player.imm_level:
            if old_player.session:
                raise DataError("Please promote (or demote} {} in game".format(old_player.name))

    def _post_update(self, player):
         update_immortal_list(player)


def check_player_perm(player, immortal):
    user = load_object(player.user_id, User)
    if not user:
        error("Missing user for player delete.")
        return
    if user.imm_level > 0:
        check_perm(immortal, 'supreme')
    else:
        check_perm(immortal, 'admin')


class UserEditor(Editor):
    def initialize(self):
        super().initialize(User, 'admin')

    def _pre_delete(self, user):
        if user.imm_level:
            raise DataError("Please remove all immortals from this account before deleting.")
        for player_id in user.player_ids:
            player = load_object(player_id, Player)
            if player and player.session:
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
