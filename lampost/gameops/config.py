from lampost.context.resource import provides, m_requires
from lampost.datastore.dbo import KeyDBO
from lampost.datastore.dbofield import DBOField
from lampost.util.lputil import javascript_safe

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'perm', 'message_service')


@provides('config_manager')
class ConfigManager():
    def __init__(self, config_id):
        self.config_id = config_id

    def start_service(self):
        register('session_connect', self._session_connect)
        register('player_create', self._player_create)
        self.config = load_object(self.config_id, Config)
        if self.config:
            perm.immortals.update({account: perm_to_level['supreme'] - 1 for account in self.system_accounts})
            self._dispatch_update()
        else:
            error("No configuration found")

    def _dispatch_update(self):
        dispatch('server_settings', self.config.server_settings)
        dispatch('game_settings', self.config.game_settings)
        dispatch('config_js', self.config_js)

    def save_config(self):
        save_object(self.config)

    def update_config(self, config_update):
        update_object(self.config, config_update)
        self._dispatch_update()

    def update_setting(self, setting_id, setting_value, setting_type='game'):
        setting_type = ''.join([setting_type, '_settings'])
        config_settings = getattr(self.config, setting_type)
        config_settings[setting_id] = setting_value

    def reserved(self, name):
        return name in self.config.system_accounts

    @property
    def system_accounts(self):
        return self.config.system_accounts

    def _player_create(self, player, user):
        if len(user.player_ids) == 1:
            player.imm_level = perm_level('creator')
            update_immortal_list(player)
            dispatch('imm_level_change', player, 0)
            message_service.add_message('system', "Welcome!  Your first player has been given creator powers.  Check out the 'Editor' window on the top menu.", player.dbo_id)
        player.room_id = self.config.start_room

    def _session_connect(self, session):
        session.append({'client_config': {'default_displays': self.config.default_displays}})

    @property
    def start_room(self):
        return self.config.start_room

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
        return self.config.dto_value


class Config(KeyDBO):
    dbo_key_type = "config"

    title = DBOField('Lampost (New Install)')
    description = DBOField('A fresh install of Lampost Mud')
    system_accounts = DBOField([], ['lampost'])
    auto_imm_level = DBOField(0)
    start_room = DBOField()
    default_displays = DBOField({})
    server_settings = DBOField({})
    game_settings = DBOField({})
