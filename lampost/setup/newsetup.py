from importlib import import_module

from lampost.context.resource import m_requires, context_post_init, register
from lampost.context.scripts import select_json
from lampost.gameops.dbconfig import Config, create
from lampost.context.config import get_value, activate
from lampost.setup import configinit

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'perm')


def new_setup(args):

    register('log', LogFactory())
    select_json()
    register('dispatcher', import_module('lampost.gameops.event'), True)
    register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)

    if args.flush:
        db_num = datastore.pool.connection_kwargs['db']
        if db_num == args.db_num:
            warn("Flushing database {}", db_num)
            datastore.redis.flushdb()
        else:
            print("Error:  DB Numbers do not match")
            return

    config = load_object(args.config_id, Config)
    if config:
        print("Error:  This instance is already set up")
        return

    room_id = "{0}:0".format(args.root_area)
    imm_name = args.imm_name.lower()

    yaml_config = configinit.load_config(args.config_dir, args.config_file)
    config = create(args.config_id, yaml_config, True)
    config.update_value('mud', 'root_area_id', args.root_area)
    config.update_value('mud', 'default_start_room', room_id)
    activate(config.section_values)

    import_module('lampost.gameops.permissions').Permissions()
    user_manager = import_module('lampost.client.user').UserManager()
    import_module('lampost.comm.channel').ChannelService()
    import_module('lampost.mud.mud').MudNature(args.flavor)
    dispatch('first_time_setup')

    create_object(import_module('lampost.model.area').Area, {'dbo_id': args.root_area, 'name': args.root_area, 'owner_id': imm_name, 'next_room_id': 1})
    create_object(import_module('lampost.env.room').Room, {'dbo_id': room_id, 'title': "Immortal Start Room", 'desc': "A brand new start room for immortals."})

    user = user_manager.create_user(args.imm_account, args.imm_password)
    player = {'dbo_id': imm_name, 'room_id': room_id, 'race': get_value('default_player_race')['dbo_id'],
              'home_room': room_id, 'imm_level': perm_level('supreme')}
    user_manager.attach_player(user, player)




