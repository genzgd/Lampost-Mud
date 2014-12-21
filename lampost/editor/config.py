import copy

from lampost.client.handlers import MethodHandler, SessionHandler
from lampost.context.resource import m_requires
from lampost.datastore.classes import get_dbo_class, subclasses
from lampost.lpflavor.skill import SkillTemplate


m_requires(__name__, 'perm', 'datastore', 'config_manager', 'context')


class ConfigEditor(MethodHandler):
    def get(self):
        check_perm(self.session, 'supreme')
        return config_manager.config_json

    def get_defaults(self):
        check_perm(self.session, 'supreme')
        return {'server': load_raw('server_settings_default'), 'game': load_raw('game_settings_default')}

    def update(self):
        check_perm(self.session, 'supreme')
        config_manager.update_config(self.raw)
        return config_manager.config_json


class DisplayEditor(MethodHandler):
    def list(self):
        return config_manager.config.default_displays

    def update(self):
        check_perm(self.session, 'admin')
        config_manager.config.default_displays = self.raw['display']
        config_manager.save_config()


class Properties(SessionHandler):
    def main(self):
        constants = copy.copy(context.properties)
        constants['features'] = [get_dbo_class(feature_id)().dto_value for feature_id in ['touchstone', 'entrance', 'store']]
        self._return(constants)


class SkillMap(SessionHandler):
    def main(self):
        skill_map = {}
        for skill_type in {skill_type for skill_type in subclasses(SkillTemplate) if hasattr(skill_type, 'dbo_key_type')}:
            skill_map.update({skill.dbo_key: {'desc': skill.desc, 'name': skill.name} for skill in load_object_set(skill_type)})
        self._return(skill_map)
