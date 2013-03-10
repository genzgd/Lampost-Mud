from lampost.editor.editor import EditorResource

from lampost.client.resources import *
from lampost.client.settings import SettingsResource

from lampost.util.lmlog import logged
from lampost.context.resource import provides, requires, m_requires

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.util import Redirect
from lampost.util.lmutil import javascript_safe

FILE_WEB_CLIENT = "ngclient"

URL_WEB_CLIENT = "ngclient"
URL_LOGIN = "login"
URL_ACTION = "action"
URL_LINK = "link"
URL_CONNECT = "connect"
URL_LSP = "lsp"
URL_EDITOR = "editor"
URL_SETTINGS = "settings"
URL_START = "/" + URL_WEB_CLIENT + "/lampost.html"

m_requires("log", __name__)

@provides('web_server')
@requires('config', 'dispatcher')
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
        self.putChild(URL_EDITOR, EditorResource())
        self.putChild(URL_SETTINGS, SettingsResource())

        self.lsp_server = LspServerResource()
        self.putChild(URL_LSP, self.lsp_server)
        self.dispatcher.register('config_updated', self._config_updated)

    #noinspection PyUnresolvedReferences
    @logged
    def _start_service(self):
        info("Starting web server", self)
        self._config_updated()
        reactor.listenTCP(self.port, Site(self), interface='127.0.0.1')
        reactor.run()

    def _config_updated(self):
        title = javascript_safe(self.config.title)
        description = javascript_safe(self.config.description)
        self.lsp_server.add_js("config.js", "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description))



