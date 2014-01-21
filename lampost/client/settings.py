import random
import string
from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.client.user import User
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.model.player import Player
from lampost.util.encrypt import make_hash, check_password
from lampost.util.lmutil import StateError

m_requires('datastore', 'user_manager', 'perm', 'email_sender', 'config_manager', 'friend_service', __name__)


class SettingsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', SettingsGet())
        self.putChild("create_account", AccountCreate())
        self.putChild('update_account', AccountUpdate())
        self.putChild('delete_account', AccountDelete())
        self.putChild('create_player', PlayerCreate())
        self.putChild('get_players', GetPlayers())
        self.putChild('delete_player', PlayerDelete())
        self.putChild('update_display', DisplayUpdate())
        self.putChild('send_name', SendAccountName())
        self.putChild('temp_password', TempPassword())
        self.putChild('set_password', SetPassword())
        self.putChild('notifies', SetNotifies())


class SettingsGet(Resource):
    @request
    def render_POST(self, content, session):
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')
        user_dto = load_object(User, content.user_id).dto_value
        user_dto['password'] = ''
        return user_dto


class AccountCreate(Resource):
    @request
    def render_POST(self, content, session):
        account_name = content.account_name.lower()
        if get_index("ix:user:name", account_name) or object_exists('player', account_name):
            raise DataError("InUse: {}".format(content.account_name))
        user = user_manager.create_user(account_name, content.password, content.email.lower())
        session.connect_user(user)
        return {'user_id': user.dbo_id}


class AccountUpdate(Resource):
    @request
    def render_POST(self, content, session):
        update_dict = content.user
        user_id = content.user_id
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')

        old_user = None
        if user_id:
            old_user = datastore.load_object(User, user_id)
            if not old_user:
                raise StateError(user_id + " does not exist!")

        if user_manager.check_name(update_dict['user_name'], old_user) != "ok":
            raise DataError("InUse: {}".format(update_dict['user_name']))
        user = User(user_id)
        if update_dict['password']:
            update_dict['password'] = make_hash(update_dict['password'])
        else:
            update_dict['password'] = old_user.password
        update_dict['email'] = update_dict['email'].lower()
        update_object(user, update_dict)


@requires('session_manager')
class AccountDelete(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        if user.player_ids and not check_password(content.password, user.password):
            raise StateError("Incorrect password.")
        response = self.session_manager.logout(session)
        user_manager.delete_user(user)
        return response


class PlayerCreate(Resource):
    @request
    def render_POST(self, content):
        user = load_object(User, content.user_id)
        if not user:
            raise DataError("User {0} does not exist".format([content.user_id]))
        player_name = content.player_name.lower()
        if player_name != user.user_name and get_index("ix:user:user_name", player_name):
            raise DataError(content.player_name + " is in use.")
        if object_exists('player', player_name):
            raise DataError(content.player_name + " is in use.")
        content.player_data['dbo_id'] = player_name
        user_manager.attach_player(user,content.player_data)


class GetPlayers(Resource):
    @request
    def render_POST(self, content):
        user = load_object(User, content.user_id)
        if not user:
            raise StateError("User {0} does not exist".format([content.user_id]))
        return player_list(user.player_ids)


class PlayerDelete(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        if not check_password(content.password, user.password):
            raise DataError("Incorrect account password")
        if not content.player_id in user.player_ids:
            raise StateError("Player not longer associated with user")
        user_manager.delete_player(user, content.player_id)
        return player_list(user.player_ids)


class DisplayUpdate(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        user.displays = content.displays
        save_object(user)


class SendAccountName(Resource):
    @request
    def render_POST(self, content, session):
        email = content.info.lower()
        user_id = get_index("ix:user:email", email)
        if not user_id:
            raise DataError("User Not Found")
        user = load_object(User, user_id.split(":")[1])
        email_msg = "Your {} account name is {}.\nThe players on this account are {}."\
            .format(config_manager.name, user.user_name,
                    ','.join([player_id.capitalize() for player_id in user.player_ids]))
        email_sender.send_targeted_email('Account/Player Names', email_msg, [user])


class TempPassword(Resource):
    @request
    def render_POST(self, content):
        user_id = get_index("ix:user:user_name", content.info.lower())
        if user_id:
            user_id = user_id.split(':')[1]
        else:
            player = load_object(Player, content.info.lower())
            if not player:
                raise DataError("Name Not Found.")
            user_id = player.user_id
        user = load_object(User, user_id)
        if not user or not user.email:
            raise DataError("No Email On File For {}".format(content.info))
        temp_pw = ''.join(random.choice(string.ascii_letters + string.digits) for _unused in range(12))
        email_msg = "Your {} temporary password is {}.\nYou will be asked to change it after you log in."\
            .format(config_manager.name, temp_pw)
        user.password = make_hash(temp_pw)
        user.password_reset = True
        save_object(user)
        email_sender.send_targeted_email('Your {} temporary password.'.format(config_manager.name), email_msg, [user])


class SetPassword(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        user.password = make_hash(content.password)
        user.password_reset = False
        save_object(user)


class SetNotifies(Resource):
    @request
    def render_POST(self, content, session):
        user = session.user
        user.notifies = content.notifies
        save_object(user)
        friend_service.update_notifies(user.dbo_id, user.notifies)


def player_list(player_ids):
    players = []
    for player_id in player_ids:
        player = load_object(Player, player_id)
        players.append({'name': player.name, 'dbo_id': player.dbo_id})
    return players
