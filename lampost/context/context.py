from tornado.ioloop import IOLoop
from tornado.web import RedirectHandler, StaticFileHandler

import lampost.client.web
import lampost.editor.web

from lampost.client.services import PlayerListService, AnyLoginService, EditUpdateService
from lampost.client.user import UserManager
from lampost.client.email import EmailSender
from lampost.comm.channel import ChannelService
from lampost.comm.message import MessageService
from lampost.context.resource import provides, context_post_init, register
from lampost.client.server import WebServer
from lampost.context.scripts import select_json
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.redisstore import RedisStore
from lampost.gameops.config import ConfigManager
from lampost.gameops.friend import FriendService
from lampost.gameops.permissions import Permissions
from lampost.gameops.script import ScriptManager
from lampost.mud.mud import MudNature
from lampost.util.logfactory import LogFactory
from lampost.util.tools import Tools


@provides('context')
class Context():

    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='lpflavor', config_id='lampost', server_interface='0.0.0.0',
                 log_level="info", log_file=None):

        self.properties = {}
        log = LogFactory(log_level, log_file).factory(self).info('Starting server with {}', locals())
        select_json()
        Tools()
        register('datastore', RedisStore(db_host, int(db_port), int(db_num), db_pw), True)
        Dispatcher()
        Permissions()
        SessionManager()
        UserManager()
        config_mgr = ConfigManager(config_id)
        EmailSender()

        ChannelService()
        FriendService()
        MessageService()
        PlayerListService()
        EditUpdateService()
        AnyLoginService()
        MudNature(flavor)
        ScriptManager()
        web_server = WebServer()
        context_post_init()

        lampost.client.web.add_endpoints(web_server)
        lampost.editor.web.add_endpoints(web_server)

        config_mgr.start_service()
        web_server.add(r"/", RedirectHandler, url="/ngclient/lampost.html")
        web_server.add(r"/ngclient/(.*)", StaticFileHandler, path="ngclient")
        web_server.start_service(int(port), server_interface)

        IOLoop.instance().start()

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
