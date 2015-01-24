from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer

from lampost.context.resource import m_requires


m_requires(__name__, 'log', 'dispatcher')


def app_log(handler):
    if debug_enabled():
        debug('{} {} {}',handler.get_status(), handler._request_summary(),
              1000.0 * handler.request.request_time())


class WebServer():
    def __init__(self):
        self.handlers = []
        self._lsp_docs = {}

    def lsp_html(self, path, content):
        self._add_lsp(path, content, 'text/html')

    def lsp_js(self, path, content):
        self._add_lsp(path, content, 'text/javascript')

    def _add_lsp(self, path, content, content_type):
        self._lsp_docs[path] = {'content': content, 'content_type': content_type}

    def add(self, regex, handler, **init_params):
        self.handlers.append((regex, handler, init_params))

    def start_service(self, port, interface):
        self.add(r"/lsp/(.*)", LspHandler, documents=self._lsp_docs)
        application = Application(self.handlers, log_function=app_log)

        info("Starting web server on port {}", port)
        http_server = HTTPServer(application)
        http_server.listen(port, interface)


class LspHandler(RequestHandler):
    def initialize(self, documents):
        self.documents = documents

    def get(self, lsp_id):
        try:
            document = self.documents[lsp_id]
            self.set_header("Content-Type", "{}; charset=UTF-8".format(document['content_type']))
            self.write(document['content'])
        except KeyError:
            self.set_status(404)
