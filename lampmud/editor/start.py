import inspect
import itertools
from importlib import import_module

from lampost.di.config import config_value
from lampost.editor.editor import ChildrenEditor, Editor
from lampost.editor.players import PlayerEditor, UserEditor
from lampost.gameops.parser import action_keywords
from lampost.gameops.script import Scriptable, Shadow, builders
from lampost.db.registry import get_dbo_class, dbo_types, implementors, instance_implementors
from lampost.server.link import link_route


from lampmud.editor.areas import AreaEditor, RoomEditor
from lampmud.editor.scripts import ScriptEditor
from lampmud.editor.shared import SocialsEditor, SkillEditor
from lampmud.env.movement import Direction
from lampmud.comm.broadcast import broadcast_types, broadcast_tokens
from lampmud.lpmud.skill import SkillTemplate

import_module('lampost.editor.admin')
import_module('lampost.editor.session')
import_module('lampost.editor.dbops')

AreaEditor()
RoomEditor()
ChildrenEditor('mobile')
ChildrenEditor('article')
PlayerEditor()
UserEditor()
SocialsEditor()
Editor('race', 'founder')
SkillEditor('attack')
SkillEditor('defense')
ScriptEditor()


@link_route('editor/constants', 'creator')
def editor_constants(**_):
    constants = {key: config_value(key) for key in ['attributes', 'resource_pools', 'equip_types', 'equip_slots', 'weapon_types',
                                                        'damage_types', 'damage_delivery', 'damage_groups', 'affinities', 'imm_levels']}
    constants['weapon_options'] = constants['weapon_types'] + [{'dbo_id': 'unused'}, {'dbo_id': 'unarmed'}, {'dbo_id': 'any'}]
    constants['skill_calculation'] = constants['attributes'] + [{'dbo_id': 'roll', 'name': 'Dice Roll'}, {'dbo_id': 'skill', 'name': 'Skill Level'}]
    constants['defense_damage_types'] = constants['damage_types'] + constants['damage_groups']
    constants['directions'] = Direction.ordered
    constants['article_load_types'] = ['equip', 'default']
    constants['broadcast_types'] = broadcast_types
    constants['broadcast_tokens'] = broadcast_tokens
    constants['skill_types'] =  [skill_template.dbo_key_type for skill_template in dbo_types(SkillTemplate)]
    constants['features'] = [get_dbo_class(feature_id)().edit_dto for feature_id in ['touchstone', 'entrance', 'store']]
    constants['action_args'] = action_keywords
    shadow_types = {}
    for class_id, cls in itertools.chain(implementors(Scriptable), instance_implementors(Scriptable)):
        shadows = [{'name': name, 'args': inspect.getargspec(member.func).args} for name, member in inspect.getmembers(cls) if isinstance(member, Shadow)]
        if shadows:
            shadow_types[class_id] = shadows
    constants['shadow_types'] = shadow_types
    constants['script_builders'] = sorted((builder.dto for builder in builders), key=lambda dto: dto['name'])
    return(constants)
