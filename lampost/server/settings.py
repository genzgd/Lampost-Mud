import random
import string

from lampost.server.handlers import MethodHandler
from lampost.server.user import User
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.context.config import m_configured
from lampost.model.player import Player
from lampost.util.encrypt import make_hash
from lampost.util.lputil import ClientError


m_requires(__name__, 'datastore', 'dispatcher', 'user_manager', 'perm', 'email_sender', 'friend_service')

m_configured(__name__, 'lampost_title')

@requires('session_manager')
class Settings(MethodHandler):

    def get_account(self):
        user_id = self.raw['user_id']
        if self.session.user.dbo_id != user_id:
            check_perm(self.player, 'admin')
        return load_object(user_id, User).edit_dto

    def create_account(self):
        account_name = self.raw['account_name'].lower()
        if get_index("ix:user:name", account_name) or object_exists('player', account_name) or\
                account_name in perm.system_accounts or object_exists('area', account_name):
            raise DataError("InUse: {}".format(account_name))
        user = user_manager.create_user(account_name, self.raw['password'], self.raw['email'].lower())
        self.session.connect_user(user)
        return {'user_id': user.dbo_id}

    def update_account(self):
        update_dict = self.raw['user']
        user_id = self.raw['user_id']
        if self.session.user.dbo_id != user_id:
            check_perm(self.player, 'admin')

        user = datastore.load_object(user_id, User)
        if not user:
            raise ClientError(user_id + " does not exist!")

        user_manager.check_name(update_dict['user_name'], user)
        if update_dict['password']:
            update_dict['password'] = make_hash(update_dict['password'])
        else:
            update_dict['password'] = user.password
        update_dict['email'] = update_dict['email'].lower()
        update_object(user, update_dict)
        dispatch('publish_edit', 'update', user)


    def delete_account(self):
        user = self.session.user
        if user.player_ids:
            user_manager.validate_password(user, self.raw['password'])
        dispatch('player_logout', self.session)
        user_manager.delete_user(user)

    def create_player(self):
        content = self._content()
        user = load_object(content.user_id, User)
        if not user:
            raise DataError("User {0} does not exist".format(content.user_id))
        player_name = content.player_name.lower()
        if (player_name != user.user_name and get_index("ix:user:user_name", player_name))\
                or object_exists('player', player_name) or object_exists('area', player_name)\
                or player_name in perm.system_accounts:
            raise DataError(content.player_name.capitalize() + " is in use.")
        content.player_data['dbo_id'] = player_name
        player = create_object(Player, content.player_data)
        user_manager.attach_player(user, player)

    def get_players(self):
        user = load_object(self.raw['user_id'], User)
        if not user:
            raise ClientError("User {} does not exist".format(self.raw['user_id']))
        return player_list(user.player_ids)

    def delete_player(self):
        user = self.session.user
        user_manager.validate_password(user, self.raw['password'])
        player_id = self.raw['player_id']
        if not player_id in user.player_ids:
            raise ClientError("Player {} longer associated with user".format(player_id))
        user_manager.delete_player(user, player_id)
        return player_list(user.player_ids)

    def update_display(self):
        self.session.user.displays = self.raw['displays']
        save_object(self.session.user)

    def send_name(self):
        email = self.raw['info'].lower()
        user_id = get_index("ix:user:email", email)
        if not user_id:
            raise DataError("User Email Not Found")
        user = load_object(user_id, User)
        email_msg = "Your {} account name is {}.\nThe players on this account are {}."\
            .format(lampost_title, user.user_name,
                    ','.join([player_id.capitalize() for player_id in user.player_ids]))
        email_sender.send_targeted_email('Account/Player Names', email_msg, [user])

    def temp_password(self):
        info = self.raw['info'].lower()
        user_id = get_index("ix:user:user_name", info)
        if not user_id:
            player = load_object(info, Player)
            if player:
                user_id = player.user_id
            else:
                raise DataError("Unknown name or account {}".format(info))
        user = load_object(user_id, User)
        if not user.email:
            raise DataError("No Email On File For {}".format(info))
        temp_pw = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
        email_msg = "Your {} temporary password is {}.\nYou will be asked to change it after you log in."\
            .format(lampost_title, temp_pw)
        user.password = make_hash(temp_pw)
        user.password_reset = True
        save_object(user)
        email_sender.send_targeted_email('Your {} temporary password.'.format(lampost_title), email_msg, [user])

    def set_password(self):
        user = self.session.user
        user.password = make_hash(self.raw['password'])
        user.password_reset = False
        save_object(user)

    def notifies(self):
        user = self.session.user
        user.notifies = self.raw['notifies']
        save_object(user)
        friend_service.update_notifies(user.dbo_id, user.notifies)


def player_list(player_ids):
    players = []
    for player_id in player_ids:
        player = load_object(player_id, Player)
        players.append({'name': player.name, 'dbo_id': player.dbo_id})
    return players
