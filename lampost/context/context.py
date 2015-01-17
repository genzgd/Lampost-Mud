from importlib import import_module

from tornado.ioloop import IOLoop
from tornado.web import RedirectHandler, StaticFileHandler

from lampost.context.config import activate
from lampost.context.resource import provides, context_post_init, register
from lampost.util.log import LogFactory
from lampost.context.scripts import select_json
from lampost.datastore.redisstore import RedisStore
from lampost.gameops.dbconfig import Config


@provides('context')
class Context():
    def __init__(self, args):
        self.properties = {}
        register('log', LogFactory())
        select_json()
        datastore = register('datastore', RedisStore(args.db_host, args.db_port, args.db_num, args.db_pw), True)
        config = datastore.load_object(args.config_id, Config)
        activate(config.section_values)

        # We import any configuration dependent modules after the configuration is loaded and activated
        # In particular this includes any class that contains DBOField configured defaults

        register('dispatcher', import_module('lampost.gameops.event'), True)

        import_module('lampost.gameops.permissions').Permissions()
        import_module('lampost.client.session').SessionManager()
        import_module('lampost.client.user').UserManager()

        import_module('lampost.client.email').EmailSender()
        import_module('lampost.comm.channel').ChannelService()
        import_module('lampost.gameops.friend').FriendService()

        import_module('lampost.comm.message').MessageService()
        client_services = import_module('lampost.client.services')
        client_services.PlayerListService()
        client_services.EditUpdateService()
        client_services.AnyLoginService()
        import_module('lampost.mud.mud').MudNature(args.flavor)
        import_module('lampost.env.instance').InstanceManager()
        import_module('lampost.util.tools').Tools()
        web_server = import_module('lampost.client.server').WebServer()

        context_post_init()

        import_module('lampost.client.web').init(web_server)
        import_module('lampost.editor.web').add_endpoints(web_server)

        web_server.add(r"/", RedirectHandler, url="/webclient/lampost.html")
        web_server.add(r"/webclient/(.*)", StaticFileHandler, path="webclient")
        web_server.start_service(args.port, args.server_interface)

        IOLoop.instance().start()

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)
