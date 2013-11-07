from lampost.context.resource import m_requires
from lampost.gameops.display import *

m_requires('datastore', __name__)


SERVER_SETTINGS_DEFAULT = [
    {'id': 'pulse_interval', 'desc': 'Base Event Pulse interval (in seconds).'
                                     '  Many actions are measured in pulses',
     'default': .1},
    {'id': 'maintenance_interval', 'desc': 'Maintenance Pulse interval (in minutes).',
     'default': 60},
    {'id': 'refresh_link_interval', 'desc': 'Internal link status check (in seconds).',
     'default': 5},
    {'id': 'broadcast_interval', 'desc': 'Broadcast to all clients of game status'
                                         ' (such as player list) in seconds.',
     'default': 30},
    {'id': 'link_dead_interval', 'desc': 'Time without a connection before a client is considered'
                                         'link dead (in seconds)',
     'default': 15},
    {'id': 'link_idle_refresh', 'desc': 'Time that a link will be refreshed by the server if no'
                                        'other activity (in seconds).',
     'default': 45},
    {'id': 'link_dead_prune', 'desc': 'Time before a link dead player will be automatically logged out '
                                      '(in seconds).',
     'default': 120}
]

GAME_SETTINGS_DEFAULT = [
    {'id': 'area_reset', 'desc' : 'Area reset time (in seconds}.', 'default': 180}
]


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
    return displays


def build_config_settings(config):
    for setting in SERVER_SETTINGS_DEFAULT:
        config.server_settings[setting['id']] = setting['default']
    save_raw('server_settings_default', SERVER_SETTINGS_DEFAULT)
    for setting in GAME_SETTINGS_DEFAULT:
        config.game_settings[setting['id']] = setting['default']
    save_raw('game_settings_default', GAME_SETTINGS_DEFAULT)





