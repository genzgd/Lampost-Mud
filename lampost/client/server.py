from tornado.web import Application, StaticFileHandler, RedirectHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from lampost.client.channel import ChannelResource
from lampost.client.clientdata import ClientDataResource
from lampost.client.messages import MessagesResource

from lampost.editor.editor import EditorResource
from lampost.client.resources import *
from lampost.client.settings import SettingsResource
from lampost.util.lmlog import logged
from lampost.context.resource import provides, requires, m_requires

FILE_WEB_CLIENT = "ngclient"

URL_WEB_CLIENT = "ngclient"

URL_LSP = "lsp"
URL_EDITOR = "editor"
URL_CLIENT_DATA = "client_data"
URL_SETTINGS = "settings"
URL_MESSAGES = "messages"
URL_CHANNEL = "channel"
URL_UNREGISTER = 'unregister'
URL_REMOTE_LOG = 'remote_log'
URL_START = "/" + URL_WEB_CLIENT + "/lampost.html"

m_requires("log", __name__)


@provides('web_server')
@requires('dispatcher')
class WebServer():
    def __init__(self, port):
        self.port = port
        self._lsp_server = LspServerResource()
        self.dispatcher.register("config_js", self._update_config)

    def _update_config(self, config_js):
        self._lsp_server.add_js("config.js", config_js)

    #noinspection PyUnresolvedReferences
    @logged
    def start_service(self, interface):
        application = Application([
            (r"/", RedirectHandler, dict(url=URL_START)),
            (r"/ngclient/(.*)", StaticFileHandler, dict(path=FILE_WEB_CLIENT)),
            (r"/lsp/(.*)", LspHandler, dict(documents=self._lsp_server.documents)),
            (r"/connect", ConnectResource),
            (r"/link", LinkResource),
            (r"/register", RegisterResource),
            (r"/unregister", UnregisterResource),
            (r"/login", LoginResource),
            (r"/action", ActionResource),
            (r"/channel/(.*)", ChannelResource)
        ])


        # self.putChild(URL_EDITOR, EditorResource())
        # self.putChild(URL_SETTINGS, SettingsResource())
        # self.putChild(URL_MESSAGES, MessagesResource())
        # self.putChild(URL_CHANNEL, ChannelResource())
        # self.putChild(URL_CLIENT_DATA, ClientDataResource())
        # self.putChild(URL_REMOTE_LOG, RemoteLogResource())


        info("Starting web server on port {}".format(self.port), self)
        http_server = HTTPServer(application)
        http_server.listen(self.port, interface)
        IOLoop.instance().start()

