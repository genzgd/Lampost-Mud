from lampost.context.resource import provides, register
from lampost.context.scripts import select_json
from lampost.datastore.redisstore import RedisStore
from lampost.gameops.event import Dispatcher
from lampost.util.lmlog import Log


@provides('context')
class DbContext():
    def __init__(self, db_host="localhost", db_port=6379, db_num=0, db_pw=None, log_level="info", log_file=None):
        self.properties = {}

        Log(log_level, log_file)
        select_json()
        Dispatcher()
        register('datastore', RedisStore(db_host, int(db_port), int(db_num), db_pw), True)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
