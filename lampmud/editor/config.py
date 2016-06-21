import inspect
import itertools

from lampost.di.config import config_value
from lampost.gameops.script import Scriptable, Shadow, decorators
from lampost.server.handlers import SessionHandler
from lampost.db.registry import get_dbo_class, dbo_types, implementors, instance_implementors

from lampmud.env.movement import Direction
from lampmud.comm.broadcast import broadcast_types, broadcast_tokens
from lampmud.lpmud.skill import SkillTemplate


class Constants(SessionHandler):
    def main(self):
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
        shadow_types = {}
        for class_id, cls in itertools.chain(implementors(Scriptable), instance_implementors(Scriptable)):
            shadows = [{'name': name, 'args': inspect.getargspec(member.func).args} for name, member in inspect.getmembers(cls) if isinstance(member, Shadow)]
            if shadows:
                shadow_types[class_id] = shadows
        constants['shadow_types'] = shadow_types
        constants['script_decorators'] = {key : value['args'] for key, value in decorators.items()}
        self._return(constants)
