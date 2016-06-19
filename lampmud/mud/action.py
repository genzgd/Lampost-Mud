from collections import defaultdict

from lampost.di.resource import Injected, module_inject, register
from lampost.gameops.action import make_action, ActionError, ActionCache

log = Injected('log')
module_inject(__name__)

_mud_actions = ActionCache()
register('mud_actions', _mud_actions)

imm_actions = set()


def mud_action(verbs, msg_class=None, **kwargs):
    def dec_wrapper(func):
        action = make_action(func, msg_class=msg_class, **kwargs)
        _mud_actions.add_unique([verbs] if isinstance(verbs, str) else verbs, action)
    return dec_wrapper


def imm_action(verbs, msg_class=None, imm_level='builder', **kwargs):
    def dec_wrapper(func):
        imm_actions.add(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class, **kwargs)
    return dec_wrapper


@mud_action('help')
def help_action(source, args, **_):
    if not args:
        source.display_line('Available actions:')
        verb_lists = ["/".join(verbs) for verbs in _mud_actions.all_actions().values()]
        return source.display_line(", ".join(sorted(verb_lists)))
    action = _mud_actions.get(args, None)
    if not action:
        raise ActionError("No matching command found")
    return getattr(action, "help_text", "No help available.")
