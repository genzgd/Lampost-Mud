import time

from lampost.context.resource import requires, provides, m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.model.player import Player
from lampost.util.encrypt import make_hash, check_password

m_requires('log', 'datastore', 'dispatcher', __name__)


class User(RootDBO):
    dbo_key_type = "user"
    dbo_set_key = "users"
    dbo_indexes = "user_name", "email"

    user_name = DBOField('')
    password = DBOField()
    password_reset = DBOField(False)
    email = DBOField('')

    player_ids = DBOField([])
    toolbar = DBOField([])
    displays = DBOField({})
    notifies = DBOField([])


@provides('user_manager')
class UserManager(object):
    def _post_init(self):
        register("user_connect", self._user_connect)
        register("player_connect", self._player_connect)

    def validate_user(self, user_name, password):
        user = self.find_user(user_name)
        if not user:
            return "not_found", None
        if not check_password(password, user.password):
            evict_object(user)
            return "not_found", None
        return "ok", user

    def find_user(self, user_name):
        user_name = unicode(user_name).lower()
        user_id = get_index("ix:user:user_name", user_name)
        if user_id:
            return load_object(User, user_id)
        player = load_object(Player, user_name)
        if player:
            unload_player(player)
            return load_object(User, player.user_id)
        return None

    def delete_user(self, user):
        for player_id in user.player_ids:
            self._player_delete(player_id)
        delete_object(user)

    def delete_player(self, user, player_id):
        self._player_delete(player_id)
        user.remove_list('player_ids', player_id)
        save_object(user)

    def attach_player(self, user, player_dto):
        player = create_object(Player, player_dto)
        user.append_list('player_ids', player.dbo_id)
        set_index('ix:player:user', player.dbo_id, user.dbo_id)
        dispatch('player_create', player)
        player.user_id = user.dbo_id
        save_object(player)
        save_object(user)
        return user

    def find_player(self, player_id):
        player = load_object(Player, player_id)
        unload_player(player)
        return player

    def create_user(self, user_name, password, email=""):
        user = {'dbo_id': db_counter('user_id'), 'user_name': user_name,
                'email': email, 'password': make_hash(unicode(password)),
                'notifies': ['friendSound', 'friendDesktop']}
        return create_object(User, user)

    def check_name(self, account_name, old_user):
        account_name = unicode(account_name).lower()
        if old_user:
            if account_name == old_user.user_name.lower():
                return "ok"
            for player_id in old_user.player_ids:
                if account_name == player_id.lower():
                    return "ok"

        if self.player_exists(account_name):
            return "player_exists"
        if get_index("ix:user:user_name", account_name):
            return "user exists"
        return "ok"

    def player_exists(self, player_id):
        return object_exists(Player.dbo_key_type, player_id)

    def user_imm_level(self, user):
        imm_levels = []
        for player_id in user.player_ids:
            player = load_object(Player, player_id)
            imm_levels.append(player.imm_level)
            unload_player(player)
        return max(imm_levels)

    def _user_connect(self, user, client_data):
        client_data.update({'user_id': user.dbo_id, 'player_ids': user.player_ids, 'displays': user.displays,
                            'password_reset': user.password_reset, 'notifies': user.notifies})

    def _player_connect(self, player, client_data):
        client_data.update({'name': player.name, 'privilege': player.imm_level})

    def login_player(self, player_id):
        player = load_object(Player, player_id)
        dispatch('player_baptise', player)
        player.last_login = int(time.time())
        if not player.created:
            player.created = player.last_login
        player.start()
        return player

    def logout_player(self, player):
        player.age += player.last_logout - player.last_login
        player.leave_env()
        player.detach()
        save_object(player)
        evict_object(player)

    def id_to_name(self, player_id):
        try:
            return unicode(player_id.capitalize())
        except AttributeError:
            pass

    def name_to_id(self, player_name):
        return unicode(player_name.lower())

    def _player_delete(self, player_id):
        delete_index('ix:player:user', player_id)
        dispatch('player_deleted', player_id)


def unload_player(player):
    if not player:
        return
    if hasattr(player, 'session'):
        return
    evict_object(player)
