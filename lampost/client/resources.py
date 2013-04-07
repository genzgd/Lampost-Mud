import cgi
from datetime import datetime

from twisted.web.resource import Resource, NoResource
from twisted.web.server import NOT_DONE_YET
from lampost.datastore.exceptions import DataError

from lampost.util.lmlog import logged
from lampost.context.resource import m_requires
from lampost.util.lmutil import build_object, PermError, StateError

m_requires('log', 'session_manager', 'client_services', 'json_decode', 'json_encode',  __name__)


def find_session_id(request):
    session_headers = request.requestHeaders.getRawHeaders('X-Lampost-Session')
    if session_headers:
        return session_headers[0]


def request(func):
    @logged
    def wrapper(self, request):
        content = build_object(json_decode(request.content.getvalue()))
        session = session_manager.get_session(find_session_id(request))
        if not session:
            return json_encode({'link_status': 'session_not_found'})
        try:
            result = func(self, content, session)
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
        content = build_object(json_decode(request.content.getvalue()))
        session_id = find_session_id(request)
        if session_id:
            return json_encode(session_manager.reconnect_session(session_id, content.player_id))
        return json_encode(session_manager.start_session())


class LoginResource(Resource):
    @request
    def render_POST(self, content, session):
        if session.user and hasattr(content, 'player_id'):
            return session_manager.start_player(session, content.player_id)
        return session_manager.login(session, content.user_id, content.password)


class LinkResource(Resource):
    @logged
    def render_POST(self, request):
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
        action = cgi.escape(content.action).strip()
        if action in ["quit", "logout", "log out"]:
            return session_manager.logout(session)
        player.parse(action)
        return session.pull_output()


class RegisterResource(Resource):
    @request
    def render_POST(self, content, session):
        return client_services.register(content.service_id, session, getattr(content, 'data', None))


class UnregisterResource(Resource):
    @request
    def render_POST(self, content, session):
        return client_services.unregister(content.service_id, session)

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