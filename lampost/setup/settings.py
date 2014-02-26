SERVER_SETTINGS_DEFAULT = {
    'pulse_interval': {'desc': 'Base Event Pulse interval (in seconds).'
                               '  Many actions are measured in pulses', 'default': .1, 'step': 0.05, 'min': 0.05},
    'maintenance_interval': {'desc': 'Maintenance Pulse interval (in minutes).', 'default': 60},
    'refresh_link_interval': {'desc': 'Internal link status check (in seconds).', 'default': 5},
    'broadcast_interval': {'desc': 'Broadcast to all clients of game status'
                                   ' (such as player list) in seconds.', 'default': 30},
    'link_dead_interval': {'desc': 'Time without a connection before a client is considered '
                                   'link dead (in seconds)', 'default': 15},
    'link_idle_refresh': {'desc': 'Time that a link will be refreshed by the server if no '
                                  'other activity (in seconds).', 'default': 45},
    'link_dead_prune': {'desc': 'Time before a link dead player will be automatically logged out '
                                '(in seconds).', 'default': 120},

}

GAME_SETTINGS_DEFAULT = {
    'script_dir': {'desc': 'Local file directory for dynamic scripts', 'default':  'lampost_scripts'},
    'area_reset': {'desc': 'Area reset time (in seconds}.', 'default': 180},
    'room_size': {'desc': 'Default room size.', 'default': 10},
}

