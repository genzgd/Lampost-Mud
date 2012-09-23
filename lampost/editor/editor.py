from twisted.web.resource import Resource
from lampost.editor.areas import AreaResource
from lampost.editor.articles import ArticleResource
from lampost.editor.mobiles import MobileResource
from lampost.editor.players import PlayerResource
from lampost.editor.rooms import RoomResource

class EditorResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('area', AreaResource())
        self.putChild('room', RoomResource())
        self.putChild('mobile', MobileResource())
        self.putChild('article', ArticleResource())
        self.putChild('player', PlayerResource())










