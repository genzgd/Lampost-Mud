import cgi
import inspect

from twisted.web.resource import Resource, NoResource
from twisted.web.server import NOT_DONE_YET
from lampost.datastore.exceptions import DataError

from lampost.util.lmlog import logged
from lampost.context.resource import m_requires, get_resource
from lampost.util.lmutil import PermError, StateError, Blank

m_requires('log', 'perm', 'session_manager', 'json_decode', 'json_encode',  __name__)


def find_session_id(request):
    session_headers = request.requestHeaders.getRawHeaders('X-Lampost-Session')
    if session_headers:
        return session_headers[0]


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


class ConnectResource(Resource):
    @logged
    def render_POST(self, request):
        content = Blank(**json_decode(request.content.getvalue()))
        session_id = find_session_id(request)
        if session_id:
            session = session_manager.reconnect_session(session_id, content.player_id)
        else:
            session = session_manager.start_session()
        return json_encode(session.pull_output())


class LoginResource(Resource):
    @request
    def render_POST(self, content, session):
        if session.user and hasattr(content, 'player_id'):
            session_manager.start_player(session, content.player_id)
        else:
            session_manager.login(session, content.user_id, content.password)
        return session.pull_output()


class LinkResource(Resource):
    @logged
    def render_POST(self, request):
        request.setHeader('Content-Type', 'application/json')
        session = session_manager.get_session(find_session_id(request))
        if not session:
            return json_encode({'link_status': 'session_not_found'})
        session.attach(request)
        return NOT_DONE_YET


class ActionResource(Resource):
    @request
    def render_POST(self, content, session):
        player = session.player
        if not player:
            return {"link_status": "no_login"}
        player.parse(cgi.escape(content.action).strip())
        return session.pull_output()


class RegisterResource(Resource):
    @request
    def render_POST(self, content, session):
        get_resource(content.service_id).register(session, getattr(content, 'data', None))
        return session.pull_output()


class UnregisterResource(Resource):
    @request
    def render_POST(self, content, session):
        get_resource(content.service_id).unregister(session)
        return session.pull_output()


class LspServerResource(Resource):
    IsLeaf = True
    documents = {}

    def add_html(self, path, content):
        self._add_document(path, content, 'text/html')

    def add_js(self, path, content):
        self._add_document(path, content, 'text/javascript')

    def _add_document(self, path, content, content_type):
        self.documents[path] = {'content': content, 'content_type': content_type}

    class ChildResource(Resource):
        IsLeaf = True

        def __init__(self, document):
            Resource.__init__(self)
            self.document = document

        def render_GET(self, request):
            request.setHeader('Content-Type', self.document['content_type'])
            return self.document['content']

    @logged
    def getChild(self, path, request):
        try:
            return self.ChildResource(self.documents[path])
        except KeyError:
            return NoResource()


class RemoteLogResource(Resource):
    @logged
    def render_POST(self, request):
        warn(str(request.content.getvalue()), 'Remote')
        request.setResponseCode(204)
        return ''


