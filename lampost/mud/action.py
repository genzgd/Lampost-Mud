from collections import defaultdict

from lampost.context import resource
from lampost.gameops.action import make_action, convert_verbs, ActionError


resource.m_requires(__name__, 'log')
_mud_actions = {}

resource.register('mud_actions', _mud_actions)
imm_actions = set()


def mud_action(verbs, msg_class=None, **kwargs):
    def dec_wrapper(func):
        action = make_action(func, msg_class=msg_class, **kwargs)
        for verb in convert_verbs(verbs):
            if verb in _mud_actions:
                error("Adding mud action for existing verb {}", verb)
            else:
                _mud_actions[verb] = action
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
        action_verbs = defaultdict(list)
        for verb, action in _mud_actions.items():
            action_verbs[action].append(" ".join(list(verb)))
        verb_lists = ["/".join(verbs) for verbs in action_verbs.values()]
        return source.display_line(", ".join(sorted(verb_lists)))
    action = _mud_actions.get(args, None)
    if not action:
        raise ActionError("No matching command found")
    return getattr(action, "help_text", "No help available.")
