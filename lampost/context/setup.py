from json import JSONDecoder, JSONEncoder

from lampost.client.user import UserManager
from lampost.context.resource import register
from lampost.context.classes import ClassRegistry
from lampost.datastore.dbconn import RedisStore
from lampost.env.room import Room
from lampost.gameops.config import Config
from lampost.gameops.event import Dispatcher
from lampost.gameops.permissions import Permissions
from lampost.model.area import Area
from lampost.mud.mud import MudNature
from lampost.model.player import Player
from lampost.util.lmlog import Log

class SetupMudContext(object):
    def __init__(self, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='merc', config_id='lampost', imm_name='root', imm_account='root',
                 imm_password="password", start_area="immortal"):
        self.properties = {}
        register('context', self)
        Log("debug")
        cls_registry = ClassRegistry()
        Dispatcher()
        register('json_decode', JSONDecoder().decode)
        register('json_encode', JSONEncoder().encode)
        perm = Permissions()

        datastore = RedisStore(db_host, int(db_port), int(db_num), db_pw)

        config = datastore.load_object(Config, config_id)
        if config:
            print "Error:  This instance is already set up"
            return
        room_id = "{0}:0".format(start_area)
        config = Config(config_id)
        config.start_room = room_id
        config.default_colors['shout_channel'] = 0x109010
        config.default_colors['imm_channel'] = 0xed1c24
        datastore.save_object(config)

        MudNature(flavor)
        user_manager = UserManager()

        player = cls_registry(Player)(imm_name)

        area = cls_registry(Area)(start_area)
        area.name = start_area
        area.owner_id = player.dbo_id
        area.next_room_id = 1
        datastore.save_object(area)

        room = cls_registry(Room)(room_id)
        room.title = "Immortal Start Room"
        room.desc = "A brand new start room for immortals."
        datastore.save_object(room)
        area.rooms.append(room)
        datastore.save_object(area)

        player.room_id = room_id
        player.home_room = room_id
        player.imm_level = perm.perm_level('supreme')
        datastore.save_object(player)

        user = user_manager.create_user(imm_account, imm_password)
        user_manager.attach_player(user, player)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)


