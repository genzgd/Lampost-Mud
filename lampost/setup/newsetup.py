from lampost.client.user import UserManager
from lampost.comm.channel import ChannelService
from lampost.context.resource import m_requires, context_post_init
from lampost.env.room import Room
from lampost.gameops.config import Config, ConfigManager
from lampost.gameops.permissions import Permissions
from lampost.model.area import Area
from lampost.mud.mud import MudNature
from lampost.setup.dbcontext import DbContext
from lampost.setup.scripts import build_default_displays, build_default_settings
from lampost.setup.settings import SERVER_SETTINGS_DEFAULT, GAME_SETTINGS_DEFAULT

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

    Permissions()
    ChannelService()
    MudNature(args.flavor)
    user_manager = UserManager()
    config = load_object(Config, args.config_id)
    if config:
        print("Error:  This instance is already set up")
        return

    context_post_init()

    config = Config(args.config_id)
    config_manager = ConfigManager(args.config_id)
    config_manager.config = config
    room_id = "{0}:0".format(args.root_area)
    config.start_room = room_id
    config.game_settings['root_area'] = args.root_area

    config_manager.save_config()
    build_default_displays()
    build_default_settings(SERVER_SETTINGS_DEFAULT, 'server')
    build_default_settings(GAME_SETTINGS_DEFAULT, 'game')
    config_manager._dispatch_update()

    dispatch('first_time_setup')

    imm_name = args.imm_name.lower()
    imm_level = perm_level('supreme')

    area = create_object(Area, {'dbo_id': args.root_area, 'name': args.root_area, 'owner_id': args.imm_name, 'next_room_id': 1})

    room = create_object(Room, {'dbo_id': room_id, 'title': "Immortal Start Room",
                                'desc': "A brand new start room for immortals."})
    dispatch('first_room_setup', room)
    save_object(room)

    user = user_manager.create_user(args.imm_account, args.imm_password)
    player = {'dbo_id': args.imm_name, 'room_id': room_id,
              'home_room': room_id, 'imm_level': imm_level}

    user_manager.attach_player(user, player)

    set_index('immortals', imm_name, imm_level)