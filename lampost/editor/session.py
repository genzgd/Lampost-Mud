from tornado.web import RequestHandler


class EditConnect(RequestHandler):
    def post(self):
        session_id = self.request.headers.get('X-Lampost-Session')


