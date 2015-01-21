from lampost.datastore.dbofield import DBOField
from lampost.lpmud.archetype import PlayerRace, Archetype
from lampost.lpmud.player import PlayerLP

from lampost.mud import mudcore
from lampost.lpmud import lpcore
from lampost.context import config, resource
from lampost.lpmud.server import NewCharacterData
from lampost.model.area import Area
from lampost.env.room import Room


def first_time_setup(args, datastore, config_values):
    _update_classes(config_values)
    root_area = config_values['root_area_id']
    room_id = "{0}:0".format(root_area)
    imm_name = args.imm_name.lower()

    datastore.create_object(Area, {'dbo_id': root_area, 'name': root_area, 'owner_id': imm_name, 'next_room_id': 1})
    datastore.create_object(Room, {'dbo_id': room_id, 'title': "Immortal Start Room", 'desc': "A brand new start room for immortals."})

    race_dto = PlayerRace.new_dto()
    race_dto.update(config_values['default_player_race'])
    race = datastore.create_object(PlayerRace, race_dto)

    supreme_level = config_values['imm_levels']['supreme']
    player = datastore.create_object(PlayerLP, {'dbo_id': imm_name, 'room_id': room_id, 'race': race.dbo_id, 'home_room': room_id, 'imm_level': supreme_level})
    lpcore._player_create(player, None)
    datastore.save_object(player)
    return player


def start_engine(args, config_values, web_server):
    _update_classes(config_values)
    resource.register('mud_core', mudcore)
    resource.register('lpmud_core', lpcore)
    web_server.add(r'/client_data/new_char', NewCharacterData)

def _update_classes(config_values):
    PlayerLP.add_dbo_fields({attr['dbo_id']: DBOField(0) for attr in config_values['attributes']})
    PlayerLP.add_dbo_fields({pool['dbo_id']: DBOField(0) for pool in config_values['resource_pools']})

