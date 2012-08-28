from twisted.web.resource import Resource, NoResource
from lampost.context.resource import provides
from lampost.util.lmlog import logged

__author__ = 'Geoff'

@provides('lsp')
class GeneratedResource(Resource):
    IsLeaf = True
    content = {'fred': 'This is fucking Fred'}

    def add_content(self, path, content):
        self.content[path] = content

    class ChildResource(Resource):
        IsLeaf = True

        def __init__(self, content):
            self.content = content

        def render_GET(self, request):
            request.setHeader('Content-Type', 'text/javascript')
            return self.content

    @logged
    def getChild(self, path, request):
        try:
            return self.ChildResource(self.content[path])
        except KeyError:
            return NoResource()


