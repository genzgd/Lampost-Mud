import os

from importlib import import_module

from tornado.ioloop import IOLoop
from tornado.web import RedirectHandler, StaticFileHandler

from lampost.di import resource, config, app
from lampost.db.redisstore import RedisStore
from lampost.db import dbconfig
from lampost.util import json
from lampost.db import permissions
from lampost.event.system import dispatcher
from lampost.gameops import friend
from lampost.server.email import email_sender
from lampost.server import web
from lampost.server import pages
from lampost.server import display
from lampost.server.services import AnyLoginService, PlayerListService, EditUpdateService
from lampost.server.session import SessionManager
from lampost.server import user
from lampost.server.channel import ChannelService
from lampost.server import message

from lampmud.server import router as main_router
from lampmud.env import instancemgr
from lampmud.editor import router as edit_router


def start(args):
    json.select_json()

    # Load and activate the database configuration
    datastore = resource.register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw))
    db_config = datastore.load_object(args.config_id, dbconfig.Config)
    config_values = config.activate(db_config.section_values)

    resource.register('dispatcher', dispatcher)
    resource.register('perm', permissions)

    app_setup = import_module('{}.appstart'.format(args.app_id))
    app_setup.start_engine(args)

    resource.register('display', display)
    resource.register('user_manager', user)
    resource.register('session_manager', SessionManager())
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

    web.add_route(r"/", RedirectHandler, url="/webclient/lampost.html")
    web.add_route("/lsp/(.*)", pages.LspHandler)
    web.add_route(r"/webclient/(.*)", StaticFileHandler, path=os.path.abspath(args.web_files))
    web.add_routes(main_router.routes)
    web.add_routes(edit_router.routes)
    web.add_routes(app_setup.app_routes())
    web.start_service(args.port, args.server_interface)

    IOLoop.instance().start()
