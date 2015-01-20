from lampost.server.handlers import MethodHandler
from lampost.context.resource import m_requires
from lampost.datastore.redisstore import RedisStore

m_requires(__name__, 'log', 'perm', 'dispatcher')

copy_dbs = {}


def _post_init():
    register('session_disconnect', _remove_db)


def _remove_db(session):
    if session in copy_dbs:
        del copy_dbs[session]


class ImportsEditor(MethodHandler):

    def set_db(self):
        check_perm(self.player, 'admin')
        content = self._content()
        db = RedisStore(content.db_host, content.db_port, content.db_num, content.db_pw)
        copy_dbs[session] = db
        del content.db_pw
        return content.__dict__
