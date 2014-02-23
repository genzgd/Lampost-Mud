import copy

from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.datastore.classes import get_sub_classes, get_dbo_class
from lampost.context.resource import requires
from lampost.editor.areas import AreaResource, RoomResource
from lampost.editor.base import EditResource
from lampost.editor.children import EditChildrenResource
from lampost.editor.config import ConfigResource
from lampost.editor.display import DisplayResource
from lampost.editor.players import PlayerResource
from lampost.editor.scripts import ScriptResource
from lampost.editor.socials import SocialsResource
from lampost.gameops.script import Script
from lampost.lpflavor.skill import SkillTemplate
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate
from lampost.model.player import Player
from lampost.model.race import PlayerRace


class EditorResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('area', AreaResource(Area))
        self.putChild('room', RoomResource())
        self.putChild('mobile', EditChildrenResource(MobileTemplate))
        self.putChild('article', EditChildrenResource(ArticleTemplate))
        self.putChild('player', PlayerResource(Player))
        self.putChild('config', ConfigResource())
        self.putChild('constants', PropertiesResource())
        self.putChild('social', SocialsResource())
        self.putChild('display', DisplayResource())
        self.putChild('race', EditResource(PlayerRace))
        self.putChild('skill', EditResource(SkillTemplate))
        self.putChild('script', ScriptResource(Script))


@requires('context')
class PropertiesResource(Resource):
    @request
    def render_POST(self):
        constants = copy.copy(self.context.properties)
        constants['features'] = [get_dbo_class(feature_id)().dto_value for feature_id in get_sub_classes('feature')]
        return constants
