from twisted.web.resource import Resource, NoResource
from lampost.context.resource import m_requires, provides, requires
from lampost.gameops.config import Config

__author__ = 'Geoff'

m_requires('datastore', 'encode', __name__)

@provides('editor')
@requires('nature')
class Editor(object):
    pass


class EditorResource(Resource):
    def getChild(self, path, request):
        return ObjectTypeResource(path)


class ObjectTypeResource(Resource):
    def __init__(self, object_type):
        Resource.__init__(self)
        self.object_type = object_type

    def getChild(self, path, request):
        return ObjectResource(self.object_type, path)


class ObjectResource(Resource):
    IsLeaf = True

    def __init__(self, object_type, id):
        Resource.__init__(self)
        self.object_type = object_type
        self.id = id

    def render_GET(self, request):
        if self.object_type == 'config':
            dbo = datastore.load_object(Config, self.id)
            return dbo.json
        return NoResource()







