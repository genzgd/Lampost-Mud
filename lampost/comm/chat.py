from lampost.action.action import ActionError
from lampost.context.resource import m_requires
from lampost.mud.action import mud_action

m_requires('sm', __name__)

TELL_COLOR = 0x00a2e8
TELL_OTHER_COLOR = 0x0033f8
SAY_COLOR = 0xe15a00

@mud_action(('t', 'tell'))
def tell(source, args, command, **ignored):
    if not args:
        raise ActionError("Tell who?")
    tell_message(source, args[0], command.partition(args[0])[2][1:])

def tell_message(source, player_id, statement):
    session = sm.user_session(player_id)
    if not session:
        return source.display_line("Cannot find " + player_id)
    player = session.player
    if not statement:
        return source.display_line("Say what to " + player.name + "?")
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", TELL_COLOR)
    source.display_line("You tell " + player.name + ", `" + statement + "'", TELL_OTHER_COLOR)

@mud_action(('r', 'reply'))
def reply(source, verb, command, **ignored):
    if not source.last_tell:
        raise ActionError("You have not received a tell recently.")
    ix = command.find(verb[0]) + len(verb[0]) + 1
    tell_message(source, source.last_tell, command[ix:])

@mud_action('say')
def say(source, command, **ignored):
    space_ix = command.find(" ")
    if space_ix == -1:
        raise ActionError("Say what?")
    statement = command[space_ix + 1:]
    source.broadcast(s="You say `{0}'".format(statement), e="{0} says, `{1}'".format(source.name, statement), color=SAY_COLOR)
