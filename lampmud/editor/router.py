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
    ('editor/edit_connect', EditConnect),
    ('editor/edit_login', EditLogin),
    ('editor/edit_logout', EditLogout),
    ('editor/constants', Constants),
    ('editor/immortal/list', ImmortalsList),
    ('editor/area/(.*)', AreaEditor),
    Route('editor/room/list/(.*)', ChildList, key_type='room'),
    ('editor/room/(.*)', RoomEditor),
    Route('editor/mobile/list/(.*)', ChildList, key_type='mobile'),
    Route('editor/mobile/(.*)', ChildrenEditor, key_type='mobile'),
    Route('editor/article/list/(.*)', ChildList, key_type='article'),
    Route('editor/article/(.*)', ChildrenEditor, key_type='article'),
    ('editor/player/(.*)', PlayerEditor),
    ('editor/social/(.*)', SocialsEditor),
    Route('editor/race/(.*)', Editor, key_type='race', create_level='founder'),
    Route('editor/attack/(.*)', SkillEditor, key_type='attack'),
    Route('editor/defense/(.*)', SkillEditor, key_type='defense'),
    Route('editor/script/list/(.*)', ChildList, key_type='script'),
    ('editor/script/(.*)', ScriptEditor),
    ('editor/imports/(.*)', ImportsEditor),
    ('editor/user/(.*)', UserEditor),
    ('editor/admin/(.*)', AdminHandler)
]
