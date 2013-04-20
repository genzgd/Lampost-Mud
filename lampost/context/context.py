from lampost.client.services import PlayerListService, AnyLoginService
from lampost.client.user import UserManager
from lampost.client.email import EmailSender
from lampost.comm.channel import ChannelService
from lampost.comm.message import MessageService
from lampost.context.classes import ClassRegistry
from lampost.context.resource import register, provides, context_post_init
from lampost.client.server import WebServer
from lampost.context.scripts import select_json
from lampost.gameops.event import Dispatcher
from lampost.client.session import SessionManager
from lampost.datastore.dbconn import RedisStore
from lampost.gameops.config import ConfigManager
from lampost.gameops.friend import FriendService
from lampost.gameops.permissions import Permissions
from lampost.util.lmlog import Log
from lampost.mud.mud import MudNature

@provides('context')
class Context(object):
    def __init__(self, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None,
                 flavor='lpflavor', config_id='lampost', server_interface='127.0.0.1',
                 log_level="info", log_file=None):
        self.properties = {}
        Log(log_level, log_file)
        select_json()
        ClassRegistry()
        Dispatcher()
        RedisStore(db_host, int(db_port), int(db_num), db_pw)
        Permissions()
        SessionManager()
        UserManager()
        ConfigManager(config_id)
        EmailSender()

        MudNature(flavor)
        ChannelService()
        FriendService()
        MessageService()
        PlayerListService()
        AnyLoginService()
        web_server = WebServer(int(port))
        context_post_init()

        web_server.start_service(server_interface)

    def set(self, key, value):
        self.properties[key] = value

    def get(self, key):
        return self.properties.get(key, None)







