from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.client.user import User
from lampost.context.resource import m_requires

__author__ = 'Geoff'

m_requires('datastore', 'user_manager', 'perm', __name__)

class GetSettings(Resource):
    @request
    def render_POST(self, content, session):
        if session.user.dbo_id != content.user_id and not can_do(session, 'admin'):
            return "Permission denied"
        user = datastore.load_object(User, content.user_id)
        user_json = user.json_obj
        user_json['password'] = ''
        return user_json


class UpdateAccount(Resource):
    @request
    def render_POST(self, content, session):
        user_json = content.user
        user_id = content.user_id
        if session.user.dbo_id != content.user_id and not can_do(session, 'admin'):
            return "Permission denied"

        old_user = None
        if user_id:
            old_user = datastore.load_object(User, user_id)
            if not old_user:
                return "User does not exist"

        name_check = user_manager.check_name(user_json['user_name'], old_user)
        if name_check != "ok":
            return "name_in_use"
        user = User(user_id)
        if not user_json['password']:
            user_json['password'] = old_user.password

        datastore.update_object(user, user_json)
        if old_user:
            datastore.delete_index("user_name_index", old_user.user_name.lower())
        datastore.set_index("user_name_index", user.user_name.lower(), user_id)
        return "success"


class SettingsResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.putChild('get', GetSettings())
        self.putChild('update_account', UpdateAccount())


