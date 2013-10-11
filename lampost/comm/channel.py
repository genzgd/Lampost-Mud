from collections import defaultdict
from lampost.client.services import ClientService
from lampost.gameops.action import make_action
from lampost.context.resource import m_requires, provides, requires
from lampost.util.lmutil import timestamp

m_requires('dispatcher', 'datastore', 'channel_service', __name__)

MAX_CHANNEL_HISTORY = 1000


class Channel(object):
    def __init__(self, verb):
        make_action(self, verb)
        self.id = verb
        self.display = "{}_display".format(verb)
        channel_service.known_channels.append(self.id)

    def __call__(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return source.display_line("Say what?")
        text = source.name + ":" + command[space_ix:]
        channel_service.dispatch_message(self.id, text)


@provides('channel_service')
class ChannelService(ClientService):

    def __init__(self):
        super(ChannelService, self).__init__()
        self.known_channels = []

    def _post_init(self):
        super(ChannelService, self)._post_init()
        register('maintenance', self._prune_channels)
        register('session_connect', self._session_connect)
        register('player_connect', self._player_connect)

    def dispatch_message(self, channel_id, text):
        message = {'id': channel_id, 'text': text}
        timestamp(message)
        for session in self.sessions:
            if channel_id in session.channel_ids:
                session.append({'channel': message})
        add_db_list(channel_key(channel_id), {'text': text, 'timestamp': message['timestamp']})

    def gen_channels(self):
        return [self._channel_messages('shout')]

    def _session_connect(self, session):
        self.register(session, None)
        session.channel_ids = (['shout'])
        session.append({'gen_channels': self.gen_channels()})

    def _channel_messages(self, channel_id):
        return {'id': channel_id, 'messages': get_db_list(channel_key(channel_id))}

    def _player_connect(self, player, client_data):
        player.session.channel_ids = set(player.active_channels)
        client_data['channels'] = [self._channel_messages(channel_id) for channel_id in player.active_channels]

    def _prune_channels(self):
        for channel_id in self.known_channels:
            trim_db_list(channel_key(channel_id), 0, MAX_CHANNEL_HISTORY)


def channel_key(channel_id):
    return 'channel:{}'.format(channel_id)
