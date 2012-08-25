from json.decoder import JSONDecoder
from json.encoder import JSONEncoder

from twisted.internet import reactor, task
from twisted.web.server import Site

from lampost.context.resource import register, provides, requires
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.client.server import RootResource
from lampost.datastore.dbconn import RedisStore
from lampost.mud.mud import MudNature
from lampost.util.lmlog import Log

@provides('context')
@requires('dispatcher')
class Context():
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None):
        Log()
        Dispatcher()
        register('decode', JSONDecoder().decode)
        register('encode', JSONEncoder().encode)
        RedisStore(db_host, db_port, db_num, db_pw)
        SessionManager()
        nature = MudNature()

        pulse = task.LoopingCall(self.dispatcher.pulse)
        pulse.start(nature.pulse_interval)

        reactor.listenTCP(port, Site(RootResource()))
        reactor.run()