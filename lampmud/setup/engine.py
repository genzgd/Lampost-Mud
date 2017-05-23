import os

from importlib import import_module

from tornado.ioloop import IOLoop
from tornado.web import RedirectHandler, StaticFileHandler

from lampost.util.logging import get_logger
from lampost.di import resource, config, app
from lampost.db.redisstore import RedisStore
from lampost.db import dbconfig
from lampost.util import json
from lampost.db import permissions
from lampost.event.system import dispatcher
from lampost.gameops import friend
from lampost.server import web
from lampost.server.link import LinkHandler
from lampost.server import pages
from lampost.server import email as email_sender
from lampost.server import display
from lampost.server.services import AnyLoginService, PlayerListService, EditUpdateService
from lampost.server import session as session_manager
from lampost.server import user
from lampost.server.channel import ChannelService
from lampost.server import message

from lampmud.env import instancemgr


def start(args):
    json.select_json()

    datastore = resource.register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw))
    db_config = datastore.load_object(args.config_id, dbconfig.Config)
    config_values = config.activate(db_config.section_values)

    resource.register('dispatcher', dispatcher)
    resource.register('perm', permissions)

    app_setup = import_module('{}.appstart'.format(args.app_id))
    app_setup.start_engine(args)

    resource.register('display', display)
    resource.register('user_manager', user)
    resource.register('session_manager', session_manager)
    resource.register('instance_manager', instancemgr)
    resource.register('email_sender', email_sender)
    resource.register('channel_service', ChannelService())
    resource.register('friend_service', friend)
    resource.register('message_service', message)
    resource.register('player_list_service', PlayerListService())
    resource.register('login_notify_service', AnyLoginService())
    resource.register('edit_update_service', EditUpdateService())

    app.start_app()

    pages.add_page(pages.LspPage('config.js', "var lampost_config = {{title:'{0}', description:'{1}'}};"
                                 .format(config_values['lampost_title'], config_values['lampost_description'])))

    tornado_logger = get_logger('tornado.general')
    tornado_logger.setLevel(args.log_level.upper())
    tornado_logger = get_logger('tornado.access')
    tornado_logger.setLevel(args.log_level.upper())
    web.service_root = args.service_root
    if args.web_files:
        web.add_raw_route("/", RedirectHandler, url="/webclient/lampost.html")
        web.add_raw_route("/webclient/(.*)", StaticFileHandler, path=os.path.abspath(args.web_files))
    web.add_raw_route("/lsp/(.*)", pages.LspHandler)
    web.add_raw_route("/link", LinkHandler)
    web.start_service(args.port, args.server_interface)

    IOLoop.instance().start()
