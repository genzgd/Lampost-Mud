from lampost.context.resource import provides, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.util.lmutil import javascript_safe

m_requires('datastore', 'dispatcher', __name__)

@provides('config_manager')
class ConfigManager():
    def __init__(self, config_id):
        self.config_id = config_id

    def _post_init(self):
        self.config = load_object(Config, self.config_id)
        dispatch("config_updated", self.config_js)

    def next_user_id(self):
        result = str(self.config.next_user_id)
        self.config.next_user_id += 1
        while object_exists('user', self.config.next_user_id):
            self.config.next_user_id += 1
        save_object(self.config)
        return result

    def save_config(self):
        save_object(self.config)

    def update_config(self, config_update):
        update_object(self.config, config_update)
        dispatch("config_updated", self.config_js)

    def config_player(self, player):
        player.imm_level = self.config.auto_imm_level

    def start_room(self):
        return self.config.start_room

    @property
    def client_config(self):
        return {'default_displays': self.config.default_displays}

    @property
    def config_js(self):
        title = javascript_safe(self.config.title)
        description = javascript_safe(self.config.description)
        return "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description)

    @property
    def config_json(self):
        return self.config.json_obj


class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room', 'next_user_id', 'auto_imm_level', 'default_displays')
    title = "Lampost (New Install)"
    description = "A fresh install of Lampost Mud"
    next_user_id = 1
    auto_imm_level = 0

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.default_displays = {}
