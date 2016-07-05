from lampost.gameops.action import ActionError
from lampost.di.resource import Injected, module_inject
from lampmud.mud.action import mud_action

sm = Injected('session_manager')
module_inject(__name__)


@mud_action('emote', target_class='extra')
def emote(source, target):
    source.broadcast(raw="{}{} {}".format('' if source.imm_level else ':', source.name, target))


@mud_action('tell', target_class="logged_in", obj_class="extra")
def tell(source, target, obj):
    tell_message(source, target, obj)


def tell_message(source, player, statement):
    if not statement:
        return source.display_line("Say what to " + player.name + "?")
    player.last_tell = source.dbo_id
    player.display_line(source.name + " tells you, `" + statement + "'", 'tell_from')
    source.display_line("You tell " + player.name + ", `" + statement + "'", 'tell_to')


@mud_action('reply', target_class='extra')
def reply(source, target):
    if not source.last_tell:
        raise ActionError("You have not received a tell recently.")
    session = sm.player_session(source.last_tell)
    if session:
        tell_message(source, session.player, target)
    else:
        source.last_tell = None
        return source.display_line("{} is no longer logged in".format(source.last_tell))


@mud_action('say', target_class='extra')
def say(source, target):
    source.display_line("You say, `{}'".format(target), display='say')
    source.broadcast(raw="{} says, `{}'".format(source.name, target),
                     display='say', silent=True)
