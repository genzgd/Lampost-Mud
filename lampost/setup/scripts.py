from lampost.context.resource import m_requires
from lampost.gameops.display import *

m_requires(__name__, 'datastore', 'config_manager')


def build_default_displays():
    displays = {}

    def add_display(name, desc, color):
        displays[name] = {'desc': desc, 'color': color}

    add_display(DEFAULT_DISPLAY, "Default", '#000000')
    add_display(SYSTEM_DISPLAY, "System messages", '#002288')
    add_display(ROOM_TITLE_DISPLAY, "Room titles", '#6b306b')
    add_display(ROOM_DISPLAY, "Rooms", '#ad419a')
    add_display(EXIT_DISPLAY, "Exit descriptions", '#808000')
    add_display(TELL_FROM_DISPLAY, "Tells from other players", '#00a2e8')
    add_display(TELL_TO_DISPLAY, "Tells to other players", '#0033f8')
    add_display(SAY_DISPLAY, "Say", '#e15a00')
    add_display(COMBAT_DISPLAY, "Combat Messages", '#ee0000')

    add_display('shout_channel', 'Shout Channel', '#109010')
    add_display('imm_channel', 'Immortal Channel', '#ed1c24')
    config_manager.config.default_displays = displays
    config_manager.save_config()


def build_default_settings(settings, setting_type):
    for setting_id, setting in settings.items():
        config_manager.update_setting(setting_id, setting['default'], setting_type)
    config_manager.save_config()
    default_key = ''.join([setting_type, '_settings_default'])
    defaults = load_raw(default_key, {})
    defaults.update(settings)
    save_raw(default_key, defaults)
