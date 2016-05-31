import inspect

from lampost.di import config
from lampost.gameops.script import Scriptable
from lampost.server.handlers import SessionHandler
from lampost.db.registry import get_dbo_class, dbo_types, implementors

from lampmud.env.movement import Direction
from lampmud.comm.broadcast import broadcast_types, broadcast_tokens
from lampmud.lpmud.skill import SkillTemplate


class Constants(SessionHandler):
    def main(self):
        constants = {key: config.get_value(key) for key in ['attributes', 'resource_pools', 'equip_types', 'equip_slots', 'weapon_types',
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
        shadow_types = {'any': [{'name': 'any_func', 'args': ['self']}]}
        for class_id, cls in implementors(Scriptable):
            shadows = [{'name': name, 'args': func.shadow_args.args} for name, func in inspect.getmembers(cls) if hasattr(func, 'shadow_args')]
            if shadows:
                shadow_types[class_id] = shadows
        constants['shadow_types'] = shadow_types
        self._return(constants)
