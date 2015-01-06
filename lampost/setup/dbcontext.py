from importlib import import_module

from lampost.context.resource import provides, register
from lampost.context.scripts import select_json
from lampost.datastore.redisstore import RedisStore
from lampost.util.log import LogFactory


@provides('context')
class DbContext():
    def __init__(self, args):
        self.properties = {}

        register('log', LogFactory())
        select_json()
        register('dispatcher', import_module('lampost.gameops.event'), True)
        register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
