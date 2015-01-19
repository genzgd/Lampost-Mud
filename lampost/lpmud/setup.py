from lampost.lpmud.archetype import PlayerRace

from lampost.mud import mudcore
from lampost.context import config, resource
from lampost.lpmud.server import NewCharacterData
from lampost.model.area import Area
from lampost.env.room import Room


def load_yaml(args):
    return config.load_yaml(__name__.replace('setup', 'conf').replace('.', '/'), 'lpmud')


def first_time_setup(args, datastore, config_values):
    root_area = config_values['root_area_id']
    room_id = "{0}:0".format(root_area)
    imm_name = args.imm_name.lower()
    default_race = datastore.create_object(PlayerRace, config_values['default_player_race'])
    datastore.create_object(Area, {'dbo_id': root_area, 'name': root_area, 'owner_id': imm_name, 'next_room_id': 1})
    datastore.create_object(Room, {'dbo_id': room_id, 'title': "Immortal Start Room", 'desc': "A brand new start room for immortals."})

    supreme_level = config_values['imm_levels']['supreme']
    first_player = {'dbo_id': imm_name, 'room_id': room_id, 'race': default_race.dbo_id, 'home_room': room_id, 'imm_level': supreme_level}
    return first_player


def start_engine(args, web_server):
    resource.register('mud_core', mudcore)
    web_server.add(r'/client_data/new_char', NewCharacterData)

