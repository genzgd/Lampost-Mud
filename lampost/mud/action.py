from lampost.action.action import make_action, ActionError
from lampost.util.lmutil import dump

mud_actions = []
imm_actions = []

def mud_action(verbs, msg_class=None):
    def dec_wrapper(func):
        mud_actions.append(func)
        return make_action(func, verbs, msg_class)
    return dec_wrapper

def imm_action(verbs, msg_class=None, imm_level='creator'):
    def dec_wrapper(func):
        imm_actions.append(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class)
    return dec_wrapper


@mud_action('help')
def help(source, args, **ignored):
    if not args:
        source.display_line('Available actions:')
        verb_lists = ["/".join([" ".join(list(verb)) for verb in action.verbs]) for action in mud_actions]
        return source.display_line(", ".join(sorted(verb_lists)))
    action_set = source.actions.get(args)
    if not action_set:
        raise ActionError("No matching command found")
    if len(action_set) > 1:
        raise ActionError("Multiple matching commands")
    action = iter(action_set).next()
    return getattr(action, "help_text", "No help available.")

@mud_action('score')
def score(source, **ignored):
    for line in dump(source.get_score):
        source.display_line(line)
