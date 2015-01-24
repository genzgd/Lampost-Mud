from lampost.comm.broadcast import broadcast_types, broadcast_tokens
from lampost.context import config
from lampost.env.movement import Direction

from lampost.server.handlers import MethodHandler, SessionHandler
from lampost.context.resource import m_requires
from lampost.datastore.classes import get_dbo_class, dbo_types
from lampost.lpmud.skill import SkillTemplate


m_requires(__name__, 'perm', 'datastore')


class ConfigEditor(MethodHandler):
    def get(self):
        check_perm(self.player, 'supreme')
        return config_manager.config_json

    def get_defaults(self):
        check_perm(self.player, 'supreme')
        return {'server': load_raw('server_settings_default'), 'game': load_raw('game_settings_default')}

    def update(self):
        check_perm(self.player, 'supreme')
        config_manager.update_config(self.raw)
        return config_manager.config_json


class DisplayEditor(MethodHandler):
    def list(self):
        return config_manager.config.default_displays

    def update(self):
        check_perm(self.player, 'admin')
        config_manager.config.default_displays = self.raw['display']
        config_manager.save_config()


class Properties(SessionHandler):
    def main(self):
        constants = {key: config.get_value(key) for key in ['attributes', 'resource_pools', 'equip_types', 'equip_slots', 'weapon_types',
                                                            'damage_types', 'damage_delivery', 'damage_groups', 'affinities']}
        constants['weapon_options'] = constants['weapon_types'] + [{'dbo_id': 'unused'}, {'dbo_id': 'unarmed'}, {'dbo_id': 'any'}]
        constants['defense_damage_types'] = constants['damage_types'] + constants['damage_groups']
        constants['directions'] = Direction.ordered
        constants['article_load_types'] = ['equip', 'default']
        constants['broadcast_types'] = broadcast_types
        constants['broadcast_tokens'] = broadcast_tokens
        constants['skill_types'] =  [skill_template.dbo_key_type for skill_template in dbo_types(SkillTemplate)]
        constants['features'] = [get_dbo_class(feature_id)().edit_dto for feature_id in ['touchstone', 'entrance', 'store']]
        self._return(constants)
