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
from lampost.setup.scripts import build_default_displays, build_config_settings

m_requires('datastore', 'cls_registry', 'dispatcher', 'perm', __name__)



def new_setup(db_host="localhost", db_port=6379, db_num=0, db_pw=None, flavor='lpflavor', config_id='lampost', imm_name='root', imm_account='root',
              imm_password="password", start_area="immortal"):
    DbContext(db_host=db_host, db_num=db_num, db_port=db_port, db_pw=db_pw)
    config = load_object(Config, config_id)
    if config:
        print "Error:  This instance is already set up"
        return

    Permissions()
    ChannelService()

    config = Config(config_id)
    room_id = "{0}:0".format(start_area)
    config.start_room = room_id
    config.default_displays = build_default_displays()
    build_config_settings(config)
    save_object(config)
    ConfigManager(config_id).start_service()

    MudNature(flavor)
    user_manager = UserManager()

    context_post_init()
    dispatch('first_time_setup')

    player = cls_registry(Player)(imm_name)

    area = cls_registry(Area)(start_area)
    area.name = start_area
    area.owner_id = player.dbo_id
    area.next_room_id = 1
    save_object(area)

    room = cls_registry(Room)(room_id)
    room.title = "Immortal Start Room"
    room.desc = "A brand new start room for immortals."
    save_object(room)
    area.append_map('rooms', room)
    save_object(area)

    player.room_id = room_id
    player.home_room = room_id
    player.imm_level = perm_level('supreme')
    set_index('immortals', player.dbo_id, player.imm_level)

    user = user_manager.create_user(imm_account, imm_password)
    user_manager.attach_player(user, player)






