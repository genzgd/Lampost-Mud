from lampost.client.user import UserManager
from lampost.comm.channel import ChannelService
from lampost.context.resource import m_requires, context_post_init
from lampost.env.room import Room
from lampost.gameops.config import Config, create_from_dictionary
from lampost.gameops.permissions import Permissions
from lampost.model.area import Area
from lampost.mud.mud import MudNature
from lampost.setup import init_config
from lampost.setup.dbcontext import DbContext

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'perm')


def new_setup(args):
    DbContext(args)

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

    yaml_config = init_config.load_config(args.config_file)
    config = create_from_dictionary(args.config_id, yaml_config, True)
    config.update_value('mud', 'root_area_id', args.root_area)
    config.update_value('mud', 'default_start_room', room_id)
    config.activate()

    Permissions()
    user_manager = UserManager()
    ChannelService()
    MudNature(args.flavor)
    context_post_init()

    imm_level = perm_level('supreme')

    player = {'dbo_id': imm_name, 'room_id': room_id,
              'home_room': room_id, 'imm_level': imm_level}

    user = user_manager.create_user(args.imm_account, args.imm_password)
    user_manager.attach_player(user, player)

    create_object(Area, {'dbo_id': args.root_area, 'name': args.root_area, 'owner_id': imm_name, 'next_room_id': 1})
    create_object(Room, {'dbo_id': room_id, 'title': "Immortal Start Room", 'desc': "A brand new start room for immortals."})

    dispatch('first_time_setup')
