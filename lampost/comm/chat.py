from lampost.gameops.action import ActionError
from lampost.context.resource import m_requires
from lampost.gameops.parser import parse_chat
from lampost.mud.action import mud_action

m_requires(__name__, 'session_manager', 'user_manager')


@mud_action('emote')
def emote(source, verb, command, **_):
    statement = command[len(verb[0]) + 1:]
    source.broadcast(raw="{}{} {}".format('' if source.imm_level else ':', source.name, statement))


@mud_action(('t', 'tell'))
def tell(source, verb, args, command, **_):
    if not args:
        raise ActionError("Tell who?")
    session = session_manager.player_session(user_manager.name_to_id(args[0]))
    if not session:
        raise ActionError("{} not found.".format(args[0]))
    ix = len(verb[0]) + len(args[0]) + 2
    tell_message(source, session.player, command[ix:])


def tell_message(source, player, statement):
    if not statement:
        return source.display_line("Say what to " + player.name + "?")
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", 'tell_from')
    source.display_line("You tell " + player.name + ", `" + statement + "'", 'tell_to')


@mud_action(('r', 'reply'))
def reply(source, verb, command, **_):
    if not source.last_tell:
        raise ActionError("You have not received a tell recently.")
    session = session_manager.player_session(source.last_tell)
    if session:
        tell_message(source, session.player, parse_chat(verb, command))
    else:
        source.last_tell = None
        return source.display_line("{} is no longer logged in".format(source.last_tell))


@mud_action('say')
def say(source, verb, command, **_):
    statement = parse_chat(verb, command)
    if not statement:
        raise ActionError("Say what?")
    source.display_line("You say `{}'".format(statement), display=SAY_DISPLAY)
    source.broadcast(raw="{} says, `{}'".format(source.name, statement),
                     display=SAY_DISPLAY, silent=True)
