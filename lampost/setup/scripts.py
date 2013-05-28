from lampost.context.resource import m_requires
from lampost.gameops.display import *


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




