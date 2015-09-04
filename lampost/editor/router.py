from importlib import import_module

from lampost.editor.admin import AdminHandler
from lampost.editor.areas import AreaEditor, RoomEditor
from lampost.editor.config import ConfigEditor, DisplayEditor, Properties
from lampost.editor.editor import ChildrenEditor, Editor, ChildList
from lampost.editor.imports import ImportsEditor
from lampost.editor.players import PlayerEditor, UserEditor, ImmortalsList
from lampost.editor.scripts import ScriptEditor
from lampost.editor.session import EditConnect, EditLogin, EditLogout
from lampost.editor.shared import SocialsEditor, SkillEditor
from lampost.env.room import Room
from lampost.gameops.script import ShadowScript
from lampost.lpmud.archetype import PlayerRace
from lampost.lpmud.combat import AttackTemplate, DefenseTemplate
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate


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
