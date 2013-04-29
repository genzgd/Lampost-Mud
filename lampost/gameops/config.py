from lampost.context.resource import provides, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.util.lmutil import javascript_safe

m_requires('log', 'datastore', 'dispatcher', __name__)


@provides('config_manager')
class ConfigManager():
    def __init__(self, config_id):
        self.config_id = config_id

    def _post_init(self):
        register('session_connect', self._session_connect)
        register('player_create', self._player_create)
        self.config = load_object(Config, self.config_id)
        if self.config:
            dispatch("config_updated", self.config_js)
        else:
            error("No configuration found", self)

    def save_config(self):
        save_object(self.config)

    def update_config(self, config_update):
        update_object(self.config, config_update)
        dispatch("config_updated", self.config_js)

    def _player_create(self, player):
        if not player.imm_level:
            player.imm_level = self.config.auto_imm_level
        player.room_id = self.config.start_room

    def _session_connect(self, session, connect):
        connect['client_config'] = {'default_displays': self.config.default_displays}

    @property
    def name(self):
        return self.config.title

    @property
    def config_js(self):
        title = javascript_safe(self.config.title)
        description = javascript_safe(self.config.description)
        return "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description)

    @property
    def config_json(self):
        return self.config.dbo_dict


class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room', 'auto_imm_level', 'default_displays')
    title = "Lampost (New Install)"
    description = "A fresh install of Lampost Mud"
    auto_imm_level = 0

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.default_displays = {}

