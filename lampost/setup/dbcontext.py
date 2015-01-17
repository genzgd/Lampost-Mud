from importlib import import_module

from lampost.context.resource import provides, register
from lampost.context.scripts import select_json
from lampost.datastore.redisstore import RedisStore
from lampost.util.log import LogFactory


@provides('context')
class DbContext():
    def __init__(self, args):
        self.properties = {}



    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
