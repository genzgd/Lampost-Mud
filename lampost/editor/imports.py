from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.dbconn import RedisStore

m_requires('log', 'perm', 'dispatcher', __name__)

copy_dbs = {}


def _post_init():
    register('session_disconnect', _remove_db)

def _remove_db(session):
    if session in copy_dbs:
        del copy_dbs[session]



class ImportsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild("set_db", SetDatabaseResource())


class SetDatabaseResource(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        db = RedisStore(content.db_host, content.db_port, content.db_num, content.db_pw)
        copy_dbs[session] = db
        del content.db_pw
        return content.__dict__
