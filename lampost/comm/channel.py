from lampost.server.services import ClientService
from lampost.gameops.action import make_action
from lampost.context.resource import m_requires
from lampost.context.config import m_configured
from lampost.util.lputil import timestamp

m_requires(__name__, 'dispatcher', 'datastore', 'channel_service')

m_configured(__name__, 'max_channel_history')


class Channel():
    def __init__(self, channel_type, instance_id=None, general=False, aliases=()):
        if instance_id == 'next':
            instance_id = db_counter('channel')
        make_action(self, (channel_type,) + aliases)
        self.id = "{}_{}".format(channel_type, instance_id) if instance_id else channel_type
        channel_service.register_channel(self.id, general)

    def __call__(self, source, command, **_):
        space_ix = command.find(" ")
        if space_ix == -1:
            return source.display_line("Say what?")
        self.send_msg(source.name + ":" + command[space_ix:])

    def send_msg(self, msg):
        channel_service.dispatch_message(self.id, msg)

    def disband(self):
        channel_service.unregister_channel(self.id)

    def remove_sub(self, player):
        player.diminish_soul(self)
        player.active_channels.remove(self.id)
        if player.session:
            channel_service.remove_sub(player.session, self.id)

    def add_sub(self, player):
        player.enhance_soul(self)
        player.active_channels.add(self.id)
        channel_service.add_sub(player.session, self.id)


class ChannelService(ClientService):

    def _post_init(self):
        super()._post_init()
        self.all_channels = fetch_set_keys('all_channels')
        self.general_channels = fetch_set_keys('general_channels')
        register('maintenance', self._prune_channels)
        register('session_connect', self._session_connect)
        register('player_connect', self._player_connect)
        register('player_logout', self._player_logout)

    def register_channel(self, channel_id, general=False):
        add_set_key('all_channels', channel_id)
        self.all_channels.add(channel_id)
        if general:
            add_set_key('general_channels', channel_id)
            self.general_channels.add(channel_id)

    def unregister_channel(self, channel_id):
        delete_set_key('all_channels', channel_id)
        self.all_channels.discard(channel_id)
        self.general_channels.discard(channel_id)

    def dispatch_message(self, channel_id, text):
        message = {'id': channel_id, 'text': text}
        timestamp(message)
        for session in self.sessions:
            if channel_id in session.channel_ids:
                session.append({'channel': message})
        add_db_list(channel_key(channel_id), {'text': text, 'timestamp': message['timestamp']})

    def add_sub(self, session, channel_id):
        session.channel_ids.add(channel_id)
        session.append({'channel_subscribe': {'id': channel_id, 'messages': get_db_list(channel_key(channel_id))}})

    def remove_sub(self, session, channel_id):
        session.channel_ids.remove(channel_id)
        session.append({'channel_unsubscribe': channel_id})

    def _session_connect(self, session, *_):
        self.register(session, None)
        if not hasattr(session, 'channel_ids'):
            session.channel_ids = set()
        for channel_id in session.channel_ids.copy():
            if channel_id not in self.general_channels:
                self.remove_sub(session, channel_id)
        for channel_id in self.general_channels:
            self.add_sub(session, channel_id)

    def _player_connect(self, player, *_):
        for channel_id in player.active_channels:
            if channel_id not in player.session.channel_ids:
                self.add_sub(player.session, channel_id)
        for channel_id in player.session.channel_ids.copy():
            if channel_id not in player.active_channels:
                self.remove_sub(player.session, channel_id)

    def _player_logout(self, session):
        self._session_connect(session)

    def _prune_channels(self):
        for channel_id in self.all_channels:
            trim_db_list(channel_key(channel_id), 0, max_channel_history)


def channel_key(channel_id):
    return 'channel:{}'.format(channel_id)
