from lampost.gameops.display import *
from lampost.gameops.action import ActionError
from lampost.context.resource import m_requires
from lampost.gameops.parser import parse_chat
from lampost.mud.action import mud_action

m_requires(__name__, 'session_manager')


@mud_action(('t', 'tell'), target_class="logged_in")
def tell(source, target, verb, command, **_):
    tell_message(source, target, parse_chat(verb, command))


def tell_message(source, player, statement):
    if not statement:
        return source.display_line("Say what to " + player.name + "?")
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", TELL_FROM_DISPLAY)
    source.display_line("You tell " + player.name + ", `" + statement + "'", TELL_TO_DISPLAY)


@mud_action(('r', 'reply'))
def reply(source, verb, command, **_):
    if not source.last_tell:
        raise ActionError("You have not received a tell recently.")
    session = session_manager.player_session(source.last_tell)
    if session:
        tell_message(source, session.player, parse_chat(verb, command))
    else:
        return source.display_line("{} is no longer logged in".format(source.last_tell))


@mud_action(("'", 'say'))
def say(source, verb, command, **_):
    statement = parse_chat(verb, command)
    if not statement:
        raise ActionError("Say what?")
    source.display_line("You say `{}'".format(statement), display=SAY_DISPLAY)
    source.broadcast(raw="{} says, `{}'".format(source.name, statement),
                     display=SAY_DISPLAY, silent=True)
