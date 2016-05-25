from importlib import import_module
from tornado.ioloop import IOLoop
from tornado.web import RedirectHandler, StaticFileHandler

from lampmud.comm.channel import ChannelService
from lampmud.comm.message import MessageService
from lampmud.context import resource, scripts, config
from lampmud.context.resource import context_post_init
from lampmud.datastore.redisstore import RedisStore
from lampmud.env.instance import InstanceManager
from lampmud.gameops import event, dbconfig, permissions
from lampmud.gameops.friend import FriendService
from lampmud.server.email import EmailSender
from lampmud.server.server import WebServer
from lampmud.server.services import AnyLoginService, PlayerListService, EditUpdateService
from lampmud.server.session import SessionManager
from lampmud.server.user import UserManager
from lampmud.server import router as main_router
from lampmud.editor import router as edit_router


def start(args):
    scripts.select_json()

    # Load and activate the database configuration
    datastore = resource.register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)
    db_config = datastore.load_object(args.config_id, dbconfig.Config)
    config_values = config.activate(db_config.section_values)

    resource.register('dispatcher', event, True)
    resource.register('perm', permissions, True)

    web_server = WebServer()

    app_setup = import_module('{}.setup'.format(args.app_id))
    app_setup.start_engine(args, config_values, web_server)

    resource.register('user_manager', UserManager())
    resource.register('session_manager', SessionManager())
    resource.register('instance_manager', InstanceManager())
    resource.register('email_sender', EmailSender())
    resource.register('channel_service', ChannelService())
    resource.register('friend_service', FriendService())
    resource.register('message_service', MessageService())
    resource.register('player_list_service', PlayerListService())
    resource.register('login_notify_service', AnyLoginService())
    resource.register('edit_notify_service', EditUpdateService(), True)

    context_post_init()

    main_router.init(web_server)
    edit_router.init(web_server)

    web_server.add(r"/", RedirectHandler, url="/webclient/lampost.html")
    web_server.add(r"/webclient/(.*)", StaticFileHandler, path="webclient")
    web_server.start_service(args.port, args.server_interface)

    IOLoop.instance().start()
