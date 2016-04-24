from base64 import b64decode
import time

from lampost.context.resource import m_requires
from lampost.datastore.dbo import KeyDBO, SystemDBO
from lampost.datastore.dbofield import DBOField
from lampost.datastore.exceptions import DataError
from lampost.model.player import Player
from lampost.util.encrypt import make_hash, check_password
from lampost.util.lputil import ClientError


m_requires(__name__, 'log', 'perm', 'datastore', 'dispatcher')


class User(KeyDBO, SystemDBO):
    dbo_key_type = "user"
    dbo_set_key = "users"
    dbo_indexes = "user_name", "email"

    user_name = DBOField('')
    password = DBOField()
    password_reset = DBOField(False)
    email = DBOField('')
    notes = DBOField('')

    player_ids = DBOField([])
    displays = DBOField({})
    notifies = DBOField([])

    @property
    def edit_dto(self):
        dto = super().edit_dto
        dto['password'] = ''
        return dto

    @property
    def imm_level(self):
        if self.player_ids:
            return max([perm.immortals.get(player_id, 0) for player_id in self.player_ids])
        return 0


class UserManager():
    def _post_init(self):
        register("user_connect", self._user_connect)
        register("player_connect", self._player_connect)

    def validate_user(self, user_name, password):
        user = self.find_user(user_name)
        if not user:
            raise ClientError()
        self.validate_password(user, password)
        return user

    def validate_password(self, user, password):
        if check_password(user.password, password):
            return
        salt, old_password = user.password.split('$')
        if check_password(b64decode(bytes(old_password, 'utf-8')), password, bytes(salt, 'utf-8')):
            warn("Using old password for account {}", user.user_name)
            user.password_reset = True
            save_object(user)
        else:
            raise ClientError("invalid_password")

    def find_user(self, user_name):
        user_name = user_name.lower()
        user_id = get_index("ix:user:user_name", user_name)
        if user_id:
            return load_object(user_id, User)
        player = load_object(user_name, Player)
        if player:
            return load_object(player.user_id, User)
        return None

    def delete_user(self, user):
        for player_id in user.player_ids:
            self._player_delete(player_id)
        delete_object(user)
        dispatch('publish_edit', 'delete', user)

    def delete_player(self, user, player_id):
        if user:
            self._player_delete(player_id)
            user.player_ids.remove(player_id)
            save_object(user)

    def attach_player(self, user, player):

        user.player_ids.append(player.dbo_id)
        set_index('ix:player:user', player.dbo_id, user.dbo_id)
        dispatch('player_create', player, user)
        player.user_id = user.dbo_id
        save_object(player)
        save_object(user)
        return player

    def find_player(self, player_id):
        return load_object(player_id, Player)

    def create_user(self, user_name, password, email=""):
        user_raw = {'dbo_id': db_counter('user_id'), 'user_name': user_name,
                'email': email, 'password': make_hash(password),
                'notifies': ['friendSound', 'friendDesktop']}
        user = create_object(User, user_raw)
        dispatch('publish_edit', 'create', user)
        return user

    def check_name(self, account_name, user):
        account_name = account_name.lower()
        if user:
            if account_name == user.user_name.lower():
                return
            for player_id in user.player_ids:
                if account_name == player_id.lower():
                    return
        if self.player_exists(account_name) or get_index("ix:user:user_name", account_name):
            raise DataError("InUse: {}".format(account_name))

    def player_exists(self, player_id):
        return object_exists(Player.dbo_key_type, player_id)

    def _user_connect(self, user, client_data):
        client_data.update({'user_id': user.dbo_id, 'player_ids': user.player_ids, 'displays': user.displays,
                            'password_reset': user.password_reset, 'notifies': user.notifies})

    def _player_connect(self, player, client_data):
        client_data['name'] = player.name
        if player.imm_level:
            client_data['imm_level'] = player.imm_level

    def login_player(self, player):
        dispatch('player_baptise', player)
        player.last_login = int(time.time())
        if not player.created:
            player.created = player.last_login
        player.start()

    def logout_player(self, player):
        player.age += player.last_logout - player.last_login
        player.detach()
        save_object(player)
        evict_object(player)

    def id_to_name(self, player_id):
        try:
            return player_id.capitalize()
        except AttributeError:
            pass

    def name_to_id(self, player_name):
        return player_name.lower()

    def player_cleanup(self, player_id):
        delete_index('ix:player:user', player_id)
        for dbo_id in fetch_set_keys('owned:{}'.format(player_id)):
            dbo = load_object(dbo_id)
            if dbo and dbo.owner_id == player_id:
                dbo.change_owner()
                save_object(dbo)
                dispatch('publish_update', 'update', dbo)
        dispatch('player_deleted', player_id)

    def _player_delete(self, player_id):
        player = load_object(player_id, Player)
        if player:
            dispatch('publish_edit', 'delete', player)
            delete_object(player)
        else:
            warn("Attempting to delete player {} who does not exist.".format(player_id))
        self.player_cleanup(player_id)

