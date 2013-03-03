from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from lampost.client.user import UserManager

from lampost.context.resource import register
from lampost.context.classes import ClassRegistry
from lampost.client.server import WebServer
from lampost.gameops.config import Config
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.dbconn import RedisStore
from lampost.gameops.permissions import Permissions
from lampost.mud.mud import MudNature
from lampost.util.lmlog import Log

class Context(object):
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='merc', config_id='lampost', log_level="warn"):
        self.properties = {}
        register('context', self)
        Log(log_level)
        ClassRegistry()
        dispatcher = Dispatcher()
        register('decode', JSONDecoder().decode)
        register('encode', JSONEncoder().encode)
        datastore = RedisStore(db_host, int(db_port), int(db_num), db_pw)
        Permissions()
        SessionManager()
        UserManager()
        datastore.load_object(Config, config_id)
        web_server = WebServer(int(port))
        nature = MudNature(flavor)

        dispatcher._start_service()
        nature._start_service()
        web_server._start_service()

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)




