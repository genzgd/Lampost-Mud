from twisted.web.resource import Resource
from lampost.context.resource import m_requires, provides, requires
from lampost.editor.areas import AreaResource
from lampost.editor.rooms import RoomResource

__author__ = 'Geoff'

m_requires('datastore', 'encode', __name__)

@provides('editor')
@requires('nature')
class Editor(object):
    pass


class EditorResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('area', AreaResource())
        self.putChild('room', RoomResource())










