from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.client.user import User
from lampost.context.resource import m_requires, requires
from lampost.model.player import Player
from lampost.util.lmutil import DataError, StateError

m_requires('datastore', 'user_manager', 'perm', __name__)

class SettingsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', SettingsGet())
        self.putChild("create_account", AccountCreate())
        self.putChild('update_account', AccountUpdate())
        self.putChild('delete_account', AccountDelete())

class SettingsGet(Resource):
    @request
    def render_POST(self, content, session):
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')
        user = load_object(User, content.user_id)
        user_json = user.json_obj
        user_json['password'] = ''
        return user_json

@requires('sm', 'cls_registry')
class AccountCreate(Resource):
    @request
    def render_POST(self, content, session):
        account_name = content.account_name.lower()
        player_name = content.player_name.lower()
        if get_index("user_name_index", account_name) or object_exists('player', account_name):
            raise DataError(content.account_name + " is in use.")
        if get_index("user_name_index", player_name) or object_exists('player', player_name):
            raise DataError(content.player_name + " is in use.")
        player = self.cls_registry(Player)(player_name)
        user_manager.attach_user(player, account_name, content.password, content.email)
        return self.sm.login(session, account_name, content.password)

class AccountUpdate(Resource):
    @request
    def render_POST(self, content, session):
        user_json = content.user
        user_id = content.user_id
        if session.user.dbo_id != content.user_id:
            check_perm(session, 'admin')

        old_user = None
        if user_id:
            old_user = datastore.load_object(User, user_id)
            if not old_user:
                return "User does not exist"

        if user_manager.check_name(user_json['user_name'], old_user) != "ok":
            return "name_in_use"
        user = User(user_id)
        if not user_json['password']:
            user_json['password'] = old_user.password

        update_object(user, user_json)
        if old_user:
            delete_index("user_name_index", old_user.user_name.lower())
        set_index("user_name_index", user.user_name.lower(), user_id)
        return "success"

@requires('sm')
class AccountDelete(Resource):
    @request
    def render_POST(self, content, session):
        player = session.player
        user = load_object(User, player.user_id)
        if not user:
            raise StateError("User missing")
        if content.password != user.password:
            raise StateError("Incorrect password.")
        response = self.sm.logout(session)
        user_manager.delete_player(user, player)
        return response


