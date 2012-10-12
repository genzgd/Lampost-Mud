from lampost.gameops.action import make_action
from lampost.context.resource import requires
from lampost.dto.display import DisplayLine

@requires('dispatcher')
class Channel():
    def __init__(self, verb, color=0x000000):
        make_action(self, verb)
        self.color = color

    def __call__(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return source.display_line("Say what?")
        statement = source.name + ":" + command[space_ix:]
        self.dispatch(self, ChannelMessage(source, statement, self.color))
        source.display_line(statement, self.color)

class ChannelMessage():
    def __init__(self, source, message, color):
        self.source = source
        self.display_line = DisplayLine(message, color)
