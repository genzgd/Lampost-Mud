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
from lampost.env.instance import InstanceManager
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.redisstore import RedisStore
from lampost.gameops.config import ConfigManager
from lampost.gameops.friend import FriendService
from lampost.gameops.permissions import Permissions
from lampost.gameops.script import ScriptManager
from lampost.mud.mud import MudNature
from lampost.util.log import LogFactory
from lampost.util.tools import Tools


@provides('context')
class Context():

    def __init__(self, args):

        self.properties = {}
        register('log', LogFactory())
        select_json()
        Tools()
        register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)
        Dispatcher()
        Permissions()
        SessionManager()
        UserManager()
        config_mgr = ConfigManager(args.config_id)
        EmailSender()

        ChannelService()
        FriendService()
        MessageService()
        PlayerListService()
        EditUpdateService()
        AnyLoginService()
        MudNature(args.flavor)
        InstanceManager()
        ScriptManager()
        web_server = WebServer()
        context_post_init()

        lampost.client.web.add_endpoints(web_server)
        lampost.editor.web.add_endpoints(web_server)

        config_mgr.start_service()
        web_server.add(r"/", RedirectHandler, url="/webclient/lampost.html")
        web_server.add(r"/webclient/(.*)", StaticFileHandler, path="webclient")
        web_server.start_service(args.port, args.server_interface)

        IOLoop.instance().start()

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
