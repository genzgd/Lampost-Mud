import time

from lampost.context.resource import requires, provides, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.model.player import Player
from lampost.util.encrypt import make_hash, check_password

m_requires('log', 'datastore', __name__)


class User(RootDBO):
    dbo_key_type = "user"
    dbo_fields = "user_name", "email", "password", "password_reset", "player_ids", "toolbar", "displays", "notifies"
    dbo_set_key = "users"
    dbo_indexes = "user_name", "email"

    user_name = ""
    password = None
    password_reset = False
    email = ""

    def __init__(self, dbo_id):
        self.dbo_id = unicode(dbo_id)
        self.player_ids = []
        self.toolbar = []
        self.displays = {}
        self.notifies = []


@requires('config_manager', 'nature')
@provides('user_manager')
class UserManager(object):
    def validate_user(self, user_name, password):
        user = self.find_user(user_name)
        if not user:
            return "not_found", None
        if not check_password(password, user.password):
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
            player = load_object(Player, player_id)
            delete_object(player)
        delete_object(user)

    def delete_player(self, user, player):
        delete_object(player)
        user.player_ids.remove(player.dbo_id)
        save_object(user)

    def attach_player(self, user, player):
        user.player_ids.append(player.dbo_id)
        self.config_manager.config_player(player)
        player.user_id = user.dbo_id
        save_object(player)
        save_object(user)
        return user

    def find_player(self, player_id):
        player = load_object(Player, player_id)
        unload_player(player)
        return player

    def create_user(self, user_name, password, email=""):
        user_id = self.config_manager.next_user_id()
        user = User(user_id)
        user.user_name = unicode(user_name) if user_name else player.name
        user.password = make_hash(unicode(password))
        user.email = email
        user.player_ids = []
        save_object(user)
        return user

    def check_name(self, account_name, old_user):
        account_name = unicode(account_name).lower()
        if old_user:
            if account_name == old_user.user_name.lower():
                return "ok"
            for player_id in old_user.player_ids:
                if account_name == player_id.lower():
                    return "ok"

        player = load_object(Player, account_name)
        if player:
            unload_player(player)
            return "player_exists"
        if get_index("ix:user:user_name", account_name):
            return "user exists"
        return "ok"

    def user_imm_level(self, user):
        imm_levels = []
        for player_id in user.player_ids:
            player = load_object(Player, player_id)
            imm_levels.append(player.imm_level)
            unload_player(player)
        return max(imm_levels)

    def client_data(self, user, player=None):
        result = {'user_id': user.dbo_id, 'player_ids': user.player_ids, 'displays': user.displays,
                  'password_reset': user.password_reset, 'notifies': user.notifies}
        if player:
            result.update({'name': player.name, 'privilege': player.imm_level, 'editors': self.nature.editors(player)})
        return result

    def login_player(self, player_id):
        player = load_object(Player, player_id)
        self.nature.baptise(player)
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


def unload_player(player):
    if not player:
        return
    if hasattr(player, 'session'):
        return
    evict_object(player)