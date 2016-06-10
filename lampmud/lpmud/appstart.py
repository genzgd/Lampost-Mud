from lampost.di import resource

from lampmud.mud import mudcore

from lampmud.lpmud.server import NewCharacterData


def start_engine(args):
    resource.register('mud_core', mudcore)


def app_routes():
    return [(r'/client_data/new_char', NewCharacterData)]