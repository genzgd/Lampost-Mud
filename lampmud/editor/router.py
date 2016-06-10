from importlib import import_module

from lampost.server.route import Route

from lampost.editor.players import PlayerEditor, UserEditor, ImmortalsList
from lampost.editor.admin import AdminHandler
from lampost.editor.editor import ChildrenEditor, Editor, ChildList
from lampost.editor.session import EditConnect, EditLogin, EditLogout

from lampmud.editor.areas import AreaEditor, RoomEditor
from lampmud.editor.config import Constants
from lampmud.editor.imports import ImportsEditor
from lampmud.editor.scripts import ScriptEditor
from lampmud.editor.shared import SocialsEditor, SkillEditor

import_module('lampost.editor.dbops')

routes = [
    (r'/editor/edit_connect', EditConnect),
    (r'/editor/edit_login', EditLogin),
    (r'/editor/edit_logout', EditLogout),
    (r'/editor/constants', Constants),
    (r'/editor/immortal/list', ImmortalsList),
    (r'/editor/area/(.*)', AreaEditor),
    Route(r'/editor/room/list/(.*)', ChildList, key_type='room'),
    (r'/editor/room/(.*)', RoomEditor),
    Route(r'/editor/mobile/list/(.*)', ChildList, key_type='mobile'),
    Route(r'/editor/mobile/(.*)', ChildrenEditor, key_type='mobile'),
    Route(r'/editor/article/list/(.*)', ChildList, key_type='article'),
    Route(r'/editor/article/(.*)', ChildrenEditor, key_type='article'),
    (r'/editor/player/(.*)', PlayerEditor),
    (r'/editor/social/(.*)', SocialsEditor),
    Route(r'/editor/race/(.*)', Editor, key_type='race', create_level='founder'),
    Route(r'/editor/attack/(.*)', SkillEditor, key_type='attack'),
    Route(r'/editor/defense/(.*)', SkillEditor, key_type='defense'),
    Route(r'/editor/script/list/(.*)', ChildList, key_type='script'),
    (r'/editor/script/(.*)', ScriptEditor),
    (r'/editor/imports/(.*)', ImportsEditor),
    (r'/editor/user/(.*)', UserEditor),
    (r'/editor/admin/(.*)', AdminHandler)
]
