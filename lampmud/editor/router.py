from importlib import import_module
from lampmud.editor.players import PlayerEditor, UserEditor, ImmortalsList
from lampmud.editor.admin import AdminHandler
from lampmud.editor.areas import AreaEditor, RoomEditor
from lampmud.editor.config import ConfigEditor, DisplayEditor, Properties
from lampmud.editor.editor import ChildrenEditor, Editor, ChildList
from lampmud.editor.imports import ImportsEditor
from lampmud.editor.scripts import ScriptEditor
from lampmud.editor.session import EditConnect, EditLogin, EditLogout
from lampmud.editor.shared import SocialsEditor, SkillEditor
from lampmud.env.room import Room
from lampmud.gameops.script import ShadowScript
from lampmud.lpmud.archetype import PlayerRace
from lampmud.lpmud.combat import AttackTemplate, DefenseTemplate
from lampmud.model.article import ArticleTemplate
from lampmud.model.mobile import MobileTemplate


import_module('lampost.editor.dbops')

def init(web_server):
    web_server.add(r'/editor/edit_connect', EditConnect)
    web_server.add(r'/editor/edit_login', EditLogin)
    web_server.add(r'/editor/edit_logout', EditLogout)
    web_server.add(r'/editor/constants', Properties)
    web_server.add(r'/editor/immortal/list', ImmortalsList)
    web_server.add(r'/editor/area/(.*)', AreaEditor)
    web_server.add(r'/editor/room/list/(.*)', ChildList, obj_class=Room)
    web_server.add(r'/editor/room/(.*)', RoomEditor)
    web_server.add(r'/editor/mobile/list/(.*)', ChildList, obj_class=MobileTemplate)
    web_server.add(r'/editor/mobile/(.*)', ChildrenEditor, obj_class=MobileTemplate)
    web_server.add(r'/editor/article/list/(.*)', ChildList, obj_class=ArticleTemplate)
    web_server.add(r'/editor/article/(.*)', ChildrenEditor, obj_class=ArticleTemplate)
    web_server.add(r'/editor/player/(.*)', PlayerEditor)
    web_server.add(r'/editor/config/(.*)', ConfigEditor)
    web_server.add(r'/editor/social/(.*)', SocialsEditor)
    web_server.add(r'/editor/display/(.*)', DisplayEditor)
    web_server.add(r'/editor/race/(.*)', Editor, obj_class=PlayerRace, imm_level='founder')
    web_server.add(r'/editor/attack/(.*)', SkillEditor, obj_class=AttackTemplate)
    web_server.add(r'/editor/defense/(.*)', SkillEditor, obj_class=DefenseTemplate)
    web_server.add(r'/editor/script/list/(.*)', ChildList, obj_class=ShadowScript)
    web_server.add(r'/editor/script/(.*)', ScriptEditor)
    web_server.add(r'/editor/imports/(.*)', ImportsEditor)
    web_server.add(r'/editor/user/(.*)', UserEditor)
    web_server.add(r'/editor/admin/(.*)', AdminHandler)
