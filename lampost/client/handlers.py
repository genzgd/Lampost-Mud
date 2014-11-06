import cgi

from tornado.web import RequestHandler, asynchronous

from lampost.datastore.exceptions import DataError
from lampost.util.lmlog import logged
from lampost.context.resource import m_requires, get_resource
from lampost.util.lmutil import PermError, StateError, Blank

m_requires('log', 'perm', 'session_manager', 'json_decode', 'json_encode',  __name__)


class LinkError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code


class SessionHandler(RequestHandler):
    def _find_session(self):
        self.session = session_manager.get_session(self.request.headers.get('X-Lampost-Session'))
        if not self.session:
            raise LinkError('session_not_found')

    def _content(self):
        return Blank(**self.raw)

    def _return(self, result):
        if result:
            self.set_header('Content-Type', 'application/json')
            self.write(json_encode(result))
        else:
            self.set_status(204)
        self.finish()

    def _error(self, status, message):
        self.set_status(status, message)
        self.finish()

    @logged
    def prepare(self):
        try:
            self._find_session()
            check_perm(self.session, self)
        except LinkError as le:
            self._return({'link_status': le.error_code})
        except PermError:
            self._error(403, 'Permission denied')

    @logged
    def post(self, *args):
        try:
            self.raw = json_decode(self.request.body.decode())
        except Exception:
            self._error(400, 'Unrecognized content')
            return
        try:
            self.main(*args)
            if not self._finished:
                self._return(self.session.pull_output())
        except LinkError as le:
            self._return({'link_status': le.error_code})
        except PermError:
            self._error(403, 'Permission denied')
        except DataError as de:
            self._error(409, de.message)
        except StateError as se:
            self._error(400, se.message)
        except Exception as e:
            self._error(500, str(e))


    def main(self, *_):
        pass


class MethodHandler(SessionHandler):
    def main(self, path, *args):
        try:
            method = getattr(self, path)
            self._return(method(*args))
        except AttributeError:
            self._error(404, 'Not Found')


class Connect(RequestHandler):
    @logged
    def post(self):
        session_id = self.request.headers.get('X-Lampost-Session')
        if session_id:
            content = json_decode(self.request.body)
            session = session_manager.reconnect_session(session_id, content['player_id'])
        else:
            session = session_manager.start_session()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json_encode(session.pull_output()))


class Login(SessionHandler):
    def main(self):
        content = self._content()
        if self.session.user:
            if content.player_id:
                session_manager.start_player(self.session, content.player_id)
                return
        session_manager.login(self.session, content.user_id, content.password)


class Link(RequestHandler):
    @logged
    @asynchronous
    def post(self):
        self.set_header('Content-Type', 'application/json')
        session_id = self.request.headers.get('X-Lampost-Session')
        self.session = session_manager.get_session(session_id)
        if self.session:
            self.session.attach(self)
            return
        self.write(json_encode({'link_status': 'session_not_found'}))
        self.finish()

    def on_connection_close(self):
        if self.session:
            self.session.link_failed()


class Action(SessionHandler):
    def main(self):
        player = self.session.player
        if not player:
            raise LinkError("no_login")
        player.parse(cgi.escape(self.raw['action'].strip()))


class Register(SessionHandler):
    def main(self):
        get_resource(self.raw['service_id']).register(self.session, self.raw.get('data', None))


class Unregister(SessionHandler):
    def main(self):
        get_resource(self.raw['service_id']).unregister(self.session)


class RemoteLog(RequestHandler):
    @logged
    def post(self):
        warn(self.request.body, 'Remote')
        self.set_status(204)
