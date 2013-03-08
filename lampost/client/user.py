from lampost.context.resource import requires, provides, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.model.player import Player

m_requires('log', 'datastore', __name__)


class User(RootDBO):
    dbo_key_type = "user"
    dbo_fields =  "user_name", "email", "password", "player_ids", "toolbar"
    dbo_set_key = "users"
    dbo_indexes = "user_name"

    user_name = ""
    password = unicode("password")
    email = ""

    def __init__(self, dbo_id):
        self.dbo_id = unicode(dbo_id)
        self.player_ids = []
        self.toolbar = []


@requires('config')
@provides('user_manager')
class UserManager(object):
    def validate_user(self, user_name, password):
        user = self.find_user(user_name)
        if not user:
            return "not_found", None
        if user.password != password:
            return "not_found", None
        return "ok", user

    def find_user(self, user_name):
        user_name = unicode(user_name).lower()
        user_id = get_index("user_name_index", user_name)
        if user_id:
            return load_object(User, user_id)
        player = load_object(Player, user_name)
        if player:
            datastore.evict_object(player)
            return load_object(User, player.user_id)
        return None

    def delete_user(self, user):
        for player_id in user.player_ids:
            player = load_object(Player, player_id)
            delete_object(player)
        delete_object(user)
        delete_index("user_name_index", user.user_name)

    def delete_player(self, user, player):
        delete_object(player)
        user.player_ids.remove(player.dbo_id)
        save_object(user)

    def attach_player(self, user, player):
        user.player_ids.append(player.dbo_id)
        player.user_id = user.dbo_id
        save_object(player)
        self.save_user(user)
        return user

    def create_user(self, user_name, password, email=""):
        user_id = str(self.config.next_user_id)
        self.config.next_user_id += 1
        while object_exists('user', self.config.next_user_id):
            self.config.next_user_id += 1
        save_object(self.config)
        user = User(user_id)
        user.user_name = unicode(user_name) if user_name else player.name
        user.password = unicode(password)
        user.email = email
        user.player_ids = []
        self.save_user(user)
        return user

    def save_user(self, user):
        save_object(user)
        set_index("user_name_index", user.user_name.lower(), user.dbo_id)

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
        if get_index("user_name_index", account_name):
            return "user exists"
        return "ok"

    def user_imm_level(self, user):
        imm_levels = []
        for player_id in user.player_ids:
            player = load_object(Player, player_id)
            imm_levels.append(player.imm_level)
            unload_player(player)
        return max(imm_levels)


def unload_player(player):
    if not player:
        return
    if hasattr(player, 'session'):
        return
    evict_object(player)