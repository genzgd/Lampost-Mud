import cgi

from datetime import datetime
from lampost.client.lsp import GeneratedResource

from lampost.util.lmlog import logged
from lampost.context.resource import m_requires, provides
from lampost.dto.display import Display
from lampost.dto.link import *
from lampost.dto.rootdto import RootDTO

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.static import File
from twisted.web.util import Redirect

FILE_WEB_CLIENT = "ngclient"

URL_WEB_CLIENT = "ngclient"
URL_LOGIN = "login"
URL_ACTION = "action"
URL_LINK = "link"
URL_DIALOG = "dialog"
URL_CONNECT = "connect"
URL_GENERATED = "lsp"
URL_START = "/" + URL_WEB_CLIENT + "/lampost.html"

m_requires('sm', 'decode', 'log', __name__)


@provides('web_server')
class WebServer(Resource):
    def __init__(self, port):
        Resource.__init__(self)
        self.port = port
        self.putChild("", Redirect(URL_START))
        self.putChild(URL_WEB_CLIENT, File(FILE_WEB_CLIENT))
        self.putChild(URL_LOGIN, LoginResource())
        self.putChild(URL_LINK, LinkResource())
        self.putChild(URL_ACTION, ActionResource())
        self.putChild(URL_CONNECT, ConnectResource())
        self.putChild(URL_DIALOG, DialogResource())
        self.putChild(URL_GENERATED, GeneratedResource())

    #noinspection PyUnresolvedReferences
    @logged
    def _start_service(self):
        reactor.listenTCP(self.port, Site(self))
        reactor.run()


def request(func):
    @logged
    def wrapper(self, request):
        content = decode(request.content.getvalue())
        session_id = content.get('session_id', None)
        if not session_id:
            return LinkError(ERROR_SESSION_NOT_FOUND).json
        session = sm.get_session(session_id)
        if not session:
            return LinkError(ERROR_NO_SESSION_ID).json
        if getattr(self, 'Raw', False):
            return func(self, request, session)
        return func(self, content, session).json
    return wrapper

class ConnectResource(Resource):
    @logged
    def render_POST(self, request):
        return sm.start_session().json

class LoginResource(Resource):
    @request
    def render_POST(self, content, session):
        return sm.login(session, content['user_id'])
    
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
        action = cgi.escape(content['action']).strip()
        if action in ["quit", "logout", "log out"]:
            return sm.logout(session)
        session.activity_time = datetime.now()
        feedback = player.parse(action)
        if not feedback:
            return Display("Nothing appears to happen.")
        if getattr(feedback, "json", None):
            return feedback
        return Display(feedback)


