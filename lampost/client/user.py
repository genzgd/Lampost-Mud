from lampost.context.resource import requires, provides, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.player.player import Player

m_requires('log', 'datastore', __name__)

class User(RootDBO):
    dbo_key_type = "user"
    dbo_fields =  "user_name", "email", "password", "player_ids"
    dbo_set_key = "users"
    dbo_indexes = "user_name"

    user_name = ""
    player_ids = []
    password = "password"
    email = ""

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id


@requires('config')
@provides('user_manager')
class UserManager(object):
    def validate_user(self, user_name, password):
        user, player = self.find_user(user_name)
        if not user:
            return "not_found", None, None
        if user.password != password:
            return "not_found", None, None
        return "ok", user, player

    def find_user(self, user_name):
        user_name = user_name.lower()
        player = load_object(Player, user_name)
        if player:
            return self.find_by_player(player), player
        user_id = get_index("user_name_index", user_name)
        if user_id:
            user = load_object(User, user_id)
            player = load_object(Player, user.player_ids[0])
            return user, player
        return None, None

    def find_by_player(self, player):
        if not player.user_id:
            return self.attach_user(player)
        user = load_object(User, player.user_id)
        if not user:
            error("User not found in database for user id " + player.user_id)
            return self.attach_user(player)
        return user

    def delete_player(self, user, player):
        delete_object(player)
        user.player_ids.remove(player.dbo_id)
        if not user.player_ids:
            delete_object(user)
            delete_index("user_name_index", user.user_name)
        else:
            update_object(user)

    def attach_user(self, player, user_name=None, password="password", email="email"):
        player.user_id = str(self.config.next_user_id)
        self.config.next_user_id += 1
        user = User(player.user_id)
        user.user_name = user_name if user_name else player.name
        user.password = password
        user.email = email
        user.player_ids = [player.dbo_id]
        save_object(player)
        self.save_user(user)
        save_object(self.config)
        return user

    def save_user(self, user):
        save_object(user)
        set_index("user_name_index", user.user_name.lower(), user.dbo_id)

    def check_name(self, account_name, old_user):
        account_name = account_name.lower()
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