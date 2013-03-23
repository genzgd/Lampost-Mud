from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from lampost.context.resource import register, provides
from lampost.datastore.dbconn import RedisStore
from lampost.gameops.config import ConfigManager
from lampost.gameops.event import Dispatcher
from lampost.gameops.permissions import Permissions
from lampost.util.lmlog import Log
from lampost.context.classes import ClassRegistry


@provides('context')
class DbContext(object):
    def __init__(self, db_host="localhost", db_port=6379, db_num=0, db_pw=None, log_level="info", log_file=None):
        self.properties = {}

        register('json_decode', JSONDecoder().decode)
        register('json_encode', JSONEncoder().encode)

        Log(log_level, log_file)
        ClassRegistry()
        Dispatcher()
        RedisStore(db_host, int(db_port), int(db_num), db_pw)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)



