from lampost.di.config import config_value

from lampmud.lpmud.archetype import PlayerRace


def first_time_setup(args, db):
    root_area = config_value('root_area_id')
    room_id = "{0}:0".format(root_area)
    imm_name = args.imm_name.lower()

    db.create_object('area', {'dbo_id': root_area, 'name': root_area, 'next_room_id': 1})
    db.create_object('room', {'dbo_id': room_id, 'title': "Immortal Start Room", 'desc': "A brand new start room for immortals."})

    race_dto = PlayerRace.new_dto()
    race_dto.update(config_value('default_player_race'))
    race = db.create_object(PlayerRace, race_dto)

    supreme_level = config_value('imm_levels')['supreme']
    player = db.create_object('player', {'dbo_id': imm_name, 'room_id': room_id, 'race': race.dbo_id, 'home_room': room_id, 'imm_level': supreme_level})
    db.save_object(player)
    return player




