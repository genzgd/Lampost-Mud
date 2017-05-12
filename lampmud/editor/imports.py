from lampost.server.handlers import MethodHandler
from lampost.di.app import on_app_start
from lampost.di.resource import Injected, module_inject
from lampost.db.redisstore import RedisStore

log = Injected('log')
perm = Injected('perm')
ev = Injected('dispatcher')
module_inject(__name__)

copy_dbs = {}


@on_app_start
def _start():
    ev.register('session_disconnect', _remove_db)


def _remove_db(session):
    if session in copy_dbs:
        del copy_dbs[session]


class ImportsEditor(MethodHandler):

    def set_db(self):
        perm.check_perm(self.player, 'admin')
        content = self._content()
        db = RedisStore(content.db_host, content.db_port, content.db_num, content.db_pw)
        copy_dbs[self.session] = db
        del content.db_pw
        return content.__dict__
