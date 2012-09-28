from lampost.comm.broadcast import EnvBroadcast
from lampost.context.resource import m_requires
from lampost.dto.display import Display
from lampost.mud.action import mud_action

m_requires('sm', __name__)

TELL_COLOR = 0x00a2e8
TELL_OTHER_COLOR = 0x0033f8
SAY_COLOR = 0xe15a00

@mud_action(('t', 'tell'))
def tell(source, verb, args, command, **ignored):
    if not args:
        return "Tell who?"
    return tell_message(source, args[0], command.partition(args[0])[2][1:])

def tell_message(source, player_id, statement):
    session = sm.user_session(player_id)
    if not session:
        return "Cannot find " + player_id
    player = session.player
    if not statement:
        return "Say what to " + player.name + "?"
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", TELL_COLOR)
    return Display("You tell " + player.name + ", `" + statement + "'", TELL_OTHER_COLOR)

@mud_action(('r', 'reply'))
def reply(source, verb, command, **ignored):
    if not source.last_tell:
        return "You have not received a tell recently."
    ix = command.find(verb[0]) + len(verb[0]) + 1
    return tell_message(source, source.last_tell, command[ix:])

@mud_action('say')
def say(source, command, **ignored):
    space_ix = command.find(" ")
    if space_ix == -1:
        return "Say what?"
    statement = command[space_ix + 1:]
    return EnvBroadcast(source, "You say `{0}'".format(statement), "{0} says, `{1}'".format(source.name, statement), SAY_COLOR)
