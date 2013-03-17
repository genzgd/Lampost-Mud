from collections import defaultdict
from lampost.context.resource import provides
from lampost.gameops.action import make_action, ActionError, simple_action
from lampost.util.lmutil import dump

mud_actions = []
imm_actions = []

mud_actions.append(simple_action(("look", "l", "exa", "examine", "look at"), "examine"))


def mud_action(verbs, msg_class=None):
    def dec_wrapper(func):
        mud_actions.append(func)
        return make_action(func, verbs, msg_class)
    return dec_wrapper


def imm_action(verbs, msg_class=None, imm_level='creator', **kwargs):
    def dec_wrapper(func):
        imm_actions.append(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class, **kwargs)
    return dec_wrapper


@provides('mud_actions')
class MudActions(object):

    def __init__(self):
        self._verbs = defaultdict(set)
        for action in mud_actions:
            self.add_action(action)

    def add_action(self, action):
        for verb in getattr(action, 'verbs', []):
            self._verbs[verb].add(action)

    def rem_verb(self, verb, action):
        self._verbs.get(verb).remove(action)

    def add_verb(self, verb, action):
        self._verbs[verb].add(action)

    def verb_list(self, verb):
        return self._verbs.get(verb, [])


@mud_action('help')
def help_action(source, args, **ignored):
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
    for line in dump(source.get_score()):
        source.display_line(line)
