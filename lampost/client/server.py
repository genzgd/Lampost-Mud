from tornado.web import Application, RequestHandler
from tornado.httpserver import HTTPServer

from lampost.context.resource import m_requires, register_module


m_requires(__name__, 'log', 'dispatcher')


class WebServer():
    def __init__(self):
        self.handlers = []
        self._lsp_docs = {}
        register_module(self)

    def app_log(self, handler):
        if debug_enabled():
            debug('{} {} {}'.format(handler.get_status(), handler._request_summary(),
                                    1000.0 * handler.request.request_time()))

    def lsp_html(self, path, content):
        self._add_lsp(path, content, 'text/html')

    def lsp_js(self, path, content):
        self._add_lsp(path, content, 'text/javascript')

    def _add_lsp(self, path, content, content_type):
        self._lsp_docs[path] = {'content': content, 'content_type': content_type}

    def _post_init(self):
        register("config_js", lambda config_js : self.lsp_js('config.js', config_js))

    def add(self, regex, handler, **init_params):
        self.handlers.append((regex, handler, init_params))

    def start_service(self, port, interface):
        self.add(r"/lsp/(.*)", LspHandler, documents=self._lsp_docs)
        application = Application(self.handlers, log_function=self.app_log)

        info("Starting web server on port {}".format(port))
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
