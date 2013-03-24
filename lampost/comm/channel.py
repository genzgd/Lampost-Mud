from lampost.gameops.action import make_action
from lampost.context.resource import m_requires

m_requires('dispatcher', __name__)


class Channel():
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


class ChannelMessage():
    def __init__(self, source, text, display):
        self.source = source
        self.text = text
        self.color = display
