from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO
from lampost.util.lmutil import javascript_safe


@provides('config_manager')
@requires('datastore')
class ConfigManager():
    def __init__(self, config_id):
        self.config_id = config_id

    def _post_init(self):
        self.config = self.datastore.load_object(Config, self.config_id)
        title = javascript_safe(self.config.title)
        description = javascript_safe(self.config.description)
        self.web_server.add_lsp_js("config.js", "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description))

    def next_user_id(self):
        result = str(self.config.next_user_id)
        self.config.next_user_id += 1
        while self.datastore.object_exists('user', self.config.next_user_id):
            self.config.next_user_id += 1
        save_object(self.config)
        return result

    def update_config(self, config_update):
        self.datastore.update_object(self.config, config_update)

    def config_player(self, player):
        player.imm_level = self.config.auto_imm_level

    def start_room(self):
        return self.config.start_room

    @property
    def client_config(self):
        return {'default_colors': self.config.default_colors}

    @property
    def config_json(self):
        return self.config.json_obj


class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room', 'next_user_id', 'auto_imm_level', 'default_colors')
    title = "Lampost (New Install)"
    description = "A fresh install of Lampost Mud"
    next_user_id = 1
    auto_imm_level = 0

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.default_colors = {}
