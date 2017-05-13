from lampost.di.resource import Injected, module_inject, register
from lampost.gameops.action import make_action, ActionError, ActionCache

log = Injected('log')
module_inject(__name__)

_mud_actions = ActionCache()
register('mud_actions', _mud_actions)

imm_actions = set()


def mud_action(verbs, msg_class=None, **kwargs):
    def dec_wrapper(func):
        action = make_action(func, verbs, msg_class, **kwargs)
        _mud_actions.add_unique(action)
    return dec_wrapper


def imm_action(verbs, msg_class=None, imm_level='builder', **kwargs):
    def dec_wrapper(func):
        imm_actions.add(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class, **kwargs)
    return dec_wrapper


@mud_action('help', target_class='cmd_str_opt')
def help_action(source, target):
    if not target:
        source.display_line('Available actions:')
        verb_lists = ["/".join(verbs) for verbs in _mud_actions.all_actions().values()]
        return source.display_line(", ".join(sorted(verb_lists)))
    actions = _mud_actions.primary(target)
    if not actions:
        actions = _mud_actions.abbrev(target)
    if not actions:
        raise ActionError("No matching command found")
    if len(actions) > 1:
        raise ActionError("Multiple matching actions")
    return getattr(actions[0], "help_text", "No help available.")
