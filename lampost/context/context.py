from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from lampost.client.user import UserManager

from lampost.context.resource import register, provides, context_post_init
from lampost.context.classes import ClassRegistry
from lampost.client.server import WebServer
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.dbconn import RedisStore
from lampost.gameops.config import ConfigManager
from lampost.gameops.permissions import Permissions
from lampost.mud.mud import MudNature
from lampost.util.lmlog import Log


@provides('context')
class Context(object):
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='lpflavor', config_id='lampost', server_interface='127.0.0.1',
                 log_level="info", log_file=None):
        self.properties = {}

        register('json_decode', JSONDecoder().decode)
        register('json_encode', JSONEncoder().encode)

        Log(log_level, log_file)
        ClassRegistry()
        Dispatcher()
        RedisStore(db_host, int(db_port), int(db_num), db_pw)
        Permissions()
        SessionManager()
        UserManager()
        ConfigManager(config_id)
        MudNature(flavor)
        web_server = WebServer(int(port))

        context_post_init()

        web_server.start_service(server_interface)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)




