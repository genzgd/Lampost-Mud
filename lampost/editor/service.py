import copy
from lampost.client.handlers import SessionHandler
from lampost.context.resource import requires, m_requires
from lampost.datastore.classes import get_dbo_class, get_sub_classes
from lampost.editor.areas import AreaEditor, RoomEditor
from lampost.editor.config import ConfigEditor, DisplayEditor
from lampost.editor.editor import ChildrenEditor, Editor
from lampost.editor.imports import ImportsEditor
from lampost.editor.players import PlayerEditor
from lampost.editor.scripts import ScriptEditor
from lampost.editor.socials import SocialsEditor
from lampost.lpflavor.skill import SkillTemplate
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate
from lampost.model.race import PlayerRace

m_requires('web_server', __name__)


def _post_init():
    web_server.add(r'/editor/constants', Properties)
    web_server.add(r'/editor/area/(.*)', AreaEditor)
    web_server.add(r'/editor/room/([^/]+)(?:/(.*))', RoomEditor)
    web_server.add(r'/editor/mobile/([^/]+)(?:/(.*))?', ChildrenEditor, dict(obj_class=MobileTemplate))
    web_server.add(r'/editor/article/([^/]+)(?:/(.*))?', ChildrenEditor, dict(obj_class=ArticleTemplate))
    web_server.add(r'/editor/player/(.*)', PlayerEditor)
    web_server.add(r'/editor/config/(.*)', ConfigEditor)
    web_server.add(r'/editor/social/(.*)', SocialsEditor)
    web_server.add(r'/editor/display/(.*)', DisplayEditor)
    web_server.add(r'/editor/race/(.*)', Editor, dict(obj_class=PlayerRace))
    web_server.add(r'/editor/skill/(.*)', Editor, dict(obj_class=SkillTemplate))
    web_server.add(r'/editor/script/([^/]+)(?:/(.*))?', ScriptEditor)
    web_server.add(r'/editor/imports/(.*)', ImportsEditor)


@requires('context')
class Properties(SessionHandler):
    def main(self):
        constants = copy.copy(self.context.properties)
        constants['features'] = [get_dbo_class(feature_id)().dto_value for feature_id in get_sub_classes('feature')]
        self._return(constants)