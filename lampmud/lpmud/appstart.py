from lampost.di import resource

from lampmud.mud import mudcore
from lampmud.lpmud.combat import system


def start_engine(args):
    resource.register('action_system', system)
    resource.register('mud_core', mudcore)
