import cgi
import inspect

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

    def _return(self, result):
        if result:
            self.set_header('Content-Type', 'application/json')
            self.write(json_encode(result))

        else:
            self.set_status(204)
        self.finish()

    @logged
    def prepare(self):
        try:
            self._find_session()
            check_perm(self.session, self)
        except LinkError as le:
            self._return({'link_status': le.error_code})
        except PermError:
            self.set_status(status)(403, 'Permission denied')

    @logged
    def post(self, *args):
        try:
            self.raw = json_decode(self.request.body)
        except Exception:
            self.set_status(400, 'Unrecognized content')
            return
        try:
            self.main(*args)
            self._return(self.session.pull_output())
            return
        except LinkError as le:
            self._return({'link_status': le.error_code})
        except PermError:
            self.set_status(403, 'Permission denied')
        except DataError as de:
            self.set_status(409, de.message)
        except StateError as se:
            self.status(400, se.message)
        self.finish()

    def main(self, *_):
        pass


def request(func):
    args = set(inspect.getargspec(func).args)

    @logged
    def wrapper(self, request):
        session = session_manager.get_session(find_session_id(request))
        if not session:
            return json_encode({'link_status': 'session_not_found'})
        check_perm(session, self)

        raw = json_decode(request.content.getvalue())
        content = Blank(**raw)
        param_vars = vars()
        params = {arg_name: param_vars[arg_name] for arg_name in args}

        try:
            result = func(**params)
            if result is None:
                request.setResponseCode(204)
                return ''
            request.setHeader('Content-Type', 'application/json')
            return json_encode(result)
        except PermError:
            request.setResponseCode(403)
            return "Permission Denied."
        except DataError as de:
            request.setResponseCode(409)
            return str(de.message)
        except StateError as se:
            request.setResponseCode(400)
            return str(se.message)
    return wrapper


class ConnectResource(RequestHandler):

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


class LoginResource(SessionHandler):

    def main(self):
        if self.session.user:
            player_id = self.raw['player_id']
            if player_id:
                session_manager.start_player(self.session, player_id)
                return
        session_manager.login(self.session, self.raw['user_id'], self.raw['password'])


class LinkResource(RequestHandler):
    @logged
    @asynchronous
    def post(self):
        self.set_header('Content-Type', 'application/json')
        session_id = self.request.headers.get('X-Lampost-Session')
        self.session = session_manager.get_session(session_id)
        if self.session:
            self.session.attach(self)
        else:
            self.write(json_encode({'link_status': 'session_not_found'}))
            self.finish()

    def on_connection_close(self):
        if self.session:
            self.session.link_failed()


class ActionResource(SessionHandler):

    def main(self):
        player = self.session.player
        if not player:
            raise LinkError("no_login")
        player.parse(cgi.escape(self.raw['action'].strip()))


class RegisterResource(SessionHandler):

    def main(self):
        get_resource(self.raw['service_id']).register(self.session, getattr(self.raw, 'data', None))


class UnregisterResource(SessionHandler):

    def main(self):
        get_resource(self.raw['service_id']).unregister(self.session)


class LspServerResource():

    documents = {}

    def add_html(self, path, content):
        self._add_document(path, content, 'text/html')

    def add_js(self, path, content):
        self._add_document(path, content, 'text/javascript')

    def _add_document(self, path, content, content_type):
        self.documents[path] = {'content': content, 'content_type': content_type}


class LspHandler(RequestHandler):

    def initialize(self, documents):
        self.documents = documents

    def get(self, lsp_id):
        document = self.documents[lsp_id]
        self.set_header("Content-Type", "{}; charset=UTF-8".format(document['content_type']))
        self.write(document['content'])


class RemoteLogResource(RequestHandler):

    @logged
    def post(self):
        warn(self.request.body, 'Remote')
        self.set_status(204)



