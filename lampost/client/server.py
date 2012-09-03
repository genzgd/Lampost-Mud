from lampost.editor.editor import EditorResource

from lampost.client.resources import *
from lampost.client.settings import SettingsResource

from lampost.util.lmlog import logged
from lampost.context.resource import provides

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
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
URL_EDITOR = "editor"
URL_SETTINGS = "settings"
URL_START = "/" + URL_WEB_CLIENT + "/lampost.html"

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
        self.putChild(URL_EDITOR, EditorResource())
        self.putChild(URL_SETTINGS, SettingsResource())

    #noinspection PyUnresolvedReferences
    @logged
    def _start_service(self):
        reactor.listenTCP(self.port, Site(self))
        reactor.run()
