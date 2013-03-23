from lampost.context.resource import m_requires
from lampost.gameops.display import *


def build_default_displays():
    displays = {}

    def add_display(name, desc, color):
        displays[name] = {'desc': desc, 'color': color}

    add_display(DEFAULT_DISPLAY, "Default", 0x00000)
    add_display(SYSTEM_DISPLAY, "System messages", 0x002288)
    add_display(ROOM_TITLE_DISPLAY, "Room titles", 0x6b306b)
    add_display(ROOM_DISPLAY, "Rooms", 0xAD419A)
    add_display(EXIT_DISPLAY, "Exit descriptions", 0x808000)
    add_display(TELL_FROM_DISPLAY, "Tells from other players", 0x00a2e8)
    add_display(TELL_TO_DISPLAY, "Tells to other players", 0x0033f8)
    add_display(SAY_DISPLAY, "Say", 0xe15a00)

    add_display('shout_channel', 'Shout Channel', 0x109010)
    add_display('imm_channel', 'Immortal Channel', 0xed1c24)
    return displays




