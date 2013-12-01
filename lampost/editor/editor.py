from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import requires
from lampost.editor.areas import AreaResource, RoomResource
from lampost.editor.articles import ArticleResource
from lampost.editor.base import EditResource
from lampost.editor.config import ConfigResource
from lampost.editor.display import DisplayResource
from lampost.editor.mobiles import MobileResource
from lampost.editor.players import PlayerResource
from lampost.editor.skills import AttackResource, DefenseResource, AllSkillsResource
from lampost.editor.socials import SocialsResource
from lampost.lpflavor.combat import DefenseSkill
from lampost.model.race import PlayerRace


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
        self.putChild('display', DisplayResource())
        self.putChild('race', EditResource(PlayerRace))
        self.putChild('attack', AttackResource())
        self.putChild('defense', DefenseResource())
        self.putChild('skills', AllSkillsResource())


@requires('context')
class PropertiesResource(Resource):
    @request
    def render_POST(self):
        return self.context.properties












