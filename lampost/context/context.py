from json.decoder import JSONDecoder
from json.encoder import JSONEncoder

from lampost.context.resource import register, provides

from lampost.client.server import WebServer
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.dbconn import RedisStore
from lampost.mud.mud import MudNature
from lampost.util.lmlog import Log

@provides('context')
class Context():
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None):
        Log()
        dispatcher = Dispatcher()
        register('decode', JSONDecoder().decode)
        register('encode', JSONEncoder().encode)
        RedisStore(db_host, db_port, db_num, db_pw)
        SessionManager()
        web_server = WebServer(port)
        MudNature()

        dispatcher._start_service()
        web_server._start_service()
