from lampost.gameops.action import make_action
from lampost.context.resource import m_requires, provides, requires

m_requires('dispatcher', 'datastore', __name__)

@requires('channel_manager')
class Channel(object):
    def __init__(self, verb):
        make_action(self, verb)
        self.display = verb + "_channel"

    def __call__(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return source.display_line("Say what?")
        statement = source.name + ":" + command[space_ix:]
        dispatch(self, ChannelMessage(source, statement, self.display))
        source.display_line(statement, self.display)


class ChannelMessage(object):
    def __init__(self, source, text, display):
        self.source = source
        self.text = text
        self.color = display


@provides('channel_manager')
class ChannelManager(object):
    def _post_init(self):
        register('maintenance', self._prune_channels)

    def _prune_channels(self):
        pass
