from lampost.client.user import UserManager
from lampost.comm.channel import ChannelService
from lampost.context.resource import m_requires, context_post_init
from lampost.env.room import Room
from lampost.gameops.config import Config, ConfigManager
from lampost.gameops.permissions import Permissions
from lampost.model.area import Area
from lampost.model.player import Player
from lampost.mud.mud import MudNature
from lampost.setup.dbcontext import DbContext
from lampost.setup.scripts import build_default_displays, build_default_settings
from lampost.setup.settings import SERVER_SETTINGS_DEFAULT, GAME_SETTINGS_DEFAULT

m_requires('datastore', 'cls_registry', 'dispatcher', 'perm', __name__)


def new_setup(db_host="localhost", db_port=6379, db_num=0, db_pw=None, flavor='lpflavor', config_id='lampost', imm_name='root', imm_account='root',
              imm_password="password", start_area="immortal"):
    DbContext(db_host=db_host, db_num=db_num, db_port=db_port, db_pw=db_pw)

    Permissions()
    ChannelService()
    MudNature(flavor)
    user_manager = UserManager()
    config = load_object(Config, config_id)
    if config:
        print "Error:  This instance is already set up"
        return

    context_post_init()

    config = Config(config_id)
    config_manager = ConfigManager(config_id)
    config_manager.config = config
    room_id = "{0}:0".format(start_area)
    config.start_room = room_id
    config_manager.save_config()
    build_default_displays()
    build_default_settings(SERVER_SETTINGS_DEFAULT, 'server')
    build_default_settings(GAME_SETTINGS_DEFAULT, 'game')
    config_manager._dispatch_update()


    dispatch('first_time_setup')

    imm_name = imm_name.lower()
    imm_level = perm_level('supreme')

    area = create_object(Area, {'dbo_id': start_area, 'name': start_area, 'owner_id': imm_name})

    room = create_object(Room, {'dbo_id': room_id, 'title': "Immortal Start Room",
                                'desc': "A brand new start room for immortals."})
    dispatch('first_room_setup', room)
    save_object(room)

    area.add_room(room)

    user = user_manager.create_user(imm_account, imm_password)
    player = {'dbo_id': imm_name, 'room_id': room_id,
              'home_room': room_id, 'imm_level': imm_level}

    user_manager.attach_player(user, player)

    set_index('immortals', imm_name, imm_level)









