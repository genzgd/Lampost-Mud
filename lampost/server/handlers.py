import html

from tornado.web import RequestHandler, asynchronous

from lampost.context.resource import m_requires, get_resource
from lampost.util.lputil import ClientError, Blank

m_requires(__name__, 'log', 'perm', 'session_manager', 'json_decode', 'json_encode')


class LinkError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code


class SessionHandler(RequestHandler):
    def _handle_request_exception(self, e):
        if isinstance(e, LinkError):
            self._return({'link_status': e.error_code})
            return
        if isinstance(e, ClientError):
            self.set_status(e.http_status)
            self.write(e.client_message)
        else:
            self.set_status(500)
            exception("Handler Exception", e)
        self.finish()

    def _content(self):
        return Blank(**self.raw)

    def _return(self, result):
        if result is None:
            self.set_status(204)
        else:
            self.set_header('Content-Type', 'application/json')
            self.write(json_encode(result))
        self.finish()

    def prepare(self):
        self.session = session_manager.get_session(self.request.headers.get('X-Lampost-Session'))
        if not self.session:
            raise LinkError('session_not_found')
        self.player = self.session.player

    def post(self, *args):
        self.raw = json_decode(self.request.body.decode())
        self.main(*args)
        if not self._finished:
            self._return(self.session.pull_output())

    def main(self, *_):
        pass


class MethodHandler(SessionHandler):
    def main(self, path, *args):
        if path.startswith('_') or hasattr(SessionHandler, path):
            self.send_error(404)
            return
        method = getattr(self, path, None)
        if method:
            self._return(method(*args))
        else:
            self.send_error(404)


class GameConnect(RequestHandler):
    def post(self):
        session_id = self.request.headers.get('X-Lampost-Session')
        if session_id:
            content = json_decode(self.request.body.decode())
            session = session_manager.reconnect_session(session_id, content['player_id'])
        else:
            session = session_manager.start_session()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json_encode(session.pull_output()))


class Login(SessionHandler):
    def main(self):
        content = self._content()
        if self.session.user and getattr(content, 'player_id', None):
            session_manager.start_player(self.session, content.player_id)
        elif hasattr(content, 'user_id') and hasattr(content, 'password'):
            session_manager.login(self.session, content.user_id, content.password)
        else:
            session.append({'login_failure': 'Browser did not submit credentials, please retype'})


class Link(RequestHandler):
    @asynchronous
    def post(self):
        self.set_header('Content-Type', 'application/json')
        self.session = session_manager.get_session(self.request.headers.get('X-Lampost-Session'))
        if self.session:
            self.session.attach(self)
        else:
            self.write(json_encode({'link_status': 'session_not_found'}))
            self.finish()

    def on_connection_close(self):
        if self.session:
            self.session.link_failed("Client Connection Close")


class Action(SessionHandler):
    def main(self):
        player = self.session.player
        if not player:
            raise LinkError("no_login")
        player.parse(html.escape(self.raw['action'].strip(), False))


class Register(SessionHandler):
    def main(self):
        client_service = get_resource(self.raw['service_id'])
        if client_service:
            client_service.register(self.session, self.raw.get('data', None))
        else:
            warn("Failed to register for service {}", self.raw['service_id'])


class Unregister(SessionHandler):
    def main(self):
        get_resource(self.raw['service_id']).unregister(self.session)


class RemoteLog(RequestHandler):
    def post(self):
        warn(self.request.body, 'Remote')
        self.set_status(204)
