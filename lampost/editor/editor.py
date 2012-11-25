from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import requires
from lampost.editor.areas import AreaResource
from lampost.editor.articles import ArticleResource
from lampost.editor.config import ConfigResource
from lampost.editor.mobiles import MobileResource
from lampost.editor.players import PlayerResource
from lampost.editor.rooms import RoomResource
from lampost.editor.socials import SocialsResource

class EditorResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('area', AreaResource())
        self.putChild('room', RoomResource())
        self.putChild('mobile', MobileResource())
        self.putChild('article', ArticleResource())
        self.putChild('player', PlayerResource())
        self.putChild('config', ConfigResource())
        self.putChild('constants', PropertiesResource())
        self.putChild('socials', SocialsResource())

@requires('context')
class PropertiesResource(Resource):
    @request
    def render_POST(self, content, session):
        return self.context.properties












