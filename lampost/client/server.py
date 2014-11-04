from tornado.web import Application, StaticFileHandler, RedirectHandler, RequestHandler
from tornado.httpserver import HTTPServer

from lampost.util.lmlog import logged
from lampost.context.resource import provides, m_requires

m_requires("log", "dispatcher", __name__)


@provides('web_server')
class WebServer(object):
    def __init__(self):
        self.handlers = []
        self._lsp_docs = {}

    def lsp_html(self, path, content):
        self._add_lsp(path, content, 'text/html')

    def lsp_js(self, path, content):
        self._add_lsp(path, content, 'text/javascript')

    def _add_lsp(self, path, content, content_type):
        self._lsp_docs[path] = {'content': content, 'content_type': content_type}

    def _post_init(self):
        dispatcher.register("config_js", lambda config_js : self.lsp_js('config.js', config_js))

    def add(self, regex, handler, init_params=None):
        self.handlers.append((regex, handler, init_params))

    @logged
    def start_service(self, port, interface):
        application = Application([
            (r"/", RedirectHandler, dict(url="/ngclient/lampost.html")),
            (r"/ngclient/(.*)", StaticFileHandler, dict(path="ngclient")),
            (r"/lsp/(.*)", LspHandler, dict(documents=self._lsp_docs))
        ] + self.handlers)

        info("Starting web server on port {}".format(port), self)
        http_server = HTTPServer(application)
        http_server.listen(port, interface)


class LspHandler(RequestHandler):
    def initialize(self, documents):
        self.documents = documents

    def get(self, lsp_id):
        document = self.documents[lsp_id]
        self.set_header("Content-Type", "{}; charset=UTF-8".format(document['content_type']))
        self.write(document['content'])

