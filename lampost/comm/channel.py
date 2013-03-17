from lampost.gameops.action import make_action
from lampost.context.resource import m_requires

m_requires('dispatcher', __name__)


class Channel():
    def __init__(self, verb):
        make_action(self, verb)
        self.color = verb + "_channel"

    def __call__(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return source.display_line("Say what?")
        statement = source.name + ":" + command[space_ix:]
        dispatch(self, ChannelMessage(source, statement, self.color))
        source.display_line(statement, self.color)


class ChannelMessage():
    def __init__(self, source, text, color):
        self.source = source
        self.text = text
        self.color = color
