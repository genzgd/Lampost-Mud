from types import MethodType

def simple_action(verbs, msg_class=None):
    def execute(self, target_method, **kw_args):
        if target_method:
            return target_method(**kw_args)

    action = make_action(_ActionObject(), verbs, msg_class)
    action.execute = MethodType(execute, action)
    return action

def add_action(verbs, method, msg_class=None):
    owner = getattr(method, 'im_self')
    try:
        getattr(owner, 'providers')
    except AttributeError:
        owner.providers = set()
    action = make_action(_ActionObject(), verbs, msg_class)
    action.execute = MethodType(method, owner)
    owner.providers.add(action)
    return action

def make_action(action, verbs, msg_class=None, fixed_targets=None):
    def add_verb(verb):
        action.verbs.add(tuple(verb.split(' ')))
    try:
        getattr(action, 'verbs')
    except AttributeError:
        action.verbs = set()
    try:
        add_verb(verbs)
    except AttributeError:
        for verb in verbs:
            add_verb(verb)
    if msg_class:
        action.msg_class = "rec_{0}".format(msg_class)
    if fixed_targets:
        action.fixed_targets = fixed_targets
    return action

class ActionError(Exception):
    def __init__(self, message, color=None):
        self.message = message
        self.color = color

class _ActionObject(object):
    def __call__(self, **kwargs):
        return self.execute(**kwargs)