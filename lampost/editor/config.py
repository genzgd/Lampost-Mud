from lampost.client.handlers import MethodHandler
from lampost.context.resource import m_requires

m_requires('perm', 'datastore', 'config_manager', __name__)


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
