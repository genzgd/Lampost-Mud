import cgi
from datetime import datetime

from twisted.web.resource import Resource, NoResource
from twisted.web.server import NOT_DONE_YET

from lampost.dto.display import Display
from lampost.dto.link import *
from lampost.dto.rootdto import RootDTO
from lampost.util.lmlog import logged
from lampost.context.resource import provides, m_requires

__author__ = 'Geoff'

m_requires('sm', 'decode', 'encode', 'log', __name__)

def request(func):
    @logged
    def wrapper(self, request):
        content = RootDTO().merge_dict(decode(request.content.getvalue()))
        session_id = getattr(content, 'session_id', None)
        if not session_id:
            return LinkError(ERROR_SESSION_NOT_FOUND).json
        session = sm.get_session(session_id)
        if not session:
            return LinkError(ERROR_NO_SESSION_ID).json
        if getattr(self, 'Raw', False):
            return func(self, request, session)
        result = func(self, content, session)
        try:
            return result.json
        except AttributeError:
            if isinstance(result, dict):
                return encode(result)
            return Response(result).json
    return wrapper

class ConnectResource(Resource):
    @logged
    def render_POST(self, request):
        content = RootDTO().merge_dict(decode(request.content.getvalue()))
        session_id = getattr(content, 'session_id', None)
        if session_id:
            return sm.reconnect_session(session_id, content.player_id).json
        return sm.start_session().json

class LoginResource(Resource):
    @request
    def render_POST(self, content, session):
        return sm.login(session, content.user_id, content.password)

class LinkResource(Resource):
    Raw = True
    @request
    def render_POST(self, request, session):
        session.attach(request)
        return NOT_DONE_YET

class DialogResource(Resource):
    @request
    def render_POST(self, content, session):
        feedback = session.dialog_response(content)
        if not feedback:
            return RootDTO(silent=True)
        if getattr(feedback, "json", None):
            return feedback
        return Display(feedback)

class ActionResource(Resource):
    @request
    def render_POST(self, content, session):
        player = session.player
        if not player:
            return LinkError(ERROR_NOT_LOGGED_IN)
        action = cgi.escape(content.action).strip()
        if action in ["quit", "logout", "log out"]:
            return sm.logout(session)
        session.activity_time = datetime.now()
        feedback = player.parse(action)
        if not feedback:
            return Display("Nothing appears to happen.")
        if getattr(feedback, "json", None):
            return feedback
        return Display(feedback)

@provides('lsp')
class GeneratedResource(Resource):
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