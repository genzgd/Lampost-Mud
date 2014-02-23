from lampost.gameops.display import *
from lampost.gameops.action import ActionError
from lampost.context.resource import m_requires
from lampost.mud.action import mud_action

m_requires('session_manager', __name__)


@mud_action(('t', 'tell'))
def tell(source, args, command, **_):
    if not args:
        raise ActionError("Tell who?")
    tell_message(source, args[0], command.partition(args[0])[2][1:])


def tell_message(source, player_id, statement):
    session = session_manager.player_session(player_id)
    if not session:
        return source.display_line("Cannot find " + player_id)
    player = session.player
    if not statement:
        return source.display_line("Say what to " + player.name + "?")
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", TELL_FROM_DISPLAY)
    source.display_line("You tell " + player.name + ", `" + statement + "'", TELL_TO_DISPLAY)


@mud_action(('r', 'reply'))
def reply(source, verb, command, **_):
    if not source.last_tell:
        raise ActionError("You have not received a tell recently.")
    ix = command.find(verb[0]) + len(verb[0]) + 1
    tell_message(source, source.last_tell, command[ix:])


@mud_action('say')
def say(source, command, **_):
    space_ix = command.find(" ")
    if space_ix == -1:
        raise ActionError("Say what?")
    statement = command[space_ix + 1:]
    source.display_line("You say `{}'".format(statement), display=SAY_DISPLAY)
    source.broadcast(raw="{} says, `{}'".format(source.name, statement),
                     display=SAY_DISPLAY, silent=True)
