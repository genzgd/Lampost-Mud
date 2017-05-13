from importlib import import_module

from lampost.di import resource

from lampmud.lpmud.combat import system


def start_engine(args):
    import_module('lampmud.editor.start')
    resource.register('action_system', system)
