import inspect

from types import MethodType
from lampost.util.lmutil import PermError


def convert_verbs(verbs):
    results = set()

    def add_verb(verb):
        results.add(tuple([unicode(fragment) for fragment in verb.split(' ')]))
    try:
        add_verb(verbs)
    except AttributeError:
        for verb in verbs:
            add_verb(verb)
    return results


def simple_action(self, target_method, **kwargs):
    if target_method:
        return target_method(**kw_args)


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


def make_action(action, verbs=None, msg_class=None, prep=None, obj_msg_class=None, **kw_args):
    if verbs:
        action.verbs = getattr(action, 'verbs', set())
        action.verbs.update(convert_verbs(verbs))

    if msg_class:
        if msg_class.startswith('has_'):
            action.msg_class = msg_class[4:]
        else:
            action.msg_class = 'rec_{0}'.format(msg_class)
    elif not hasattr(action, 'msg_class'):
        try:
            args, var_args, var_kwargs, defaults = inspect.getargspec(action)
            if not args or (len(args) == 1 and args[0] == 'source'):
                action.msg_class = 'no_args'
        except TypeError:
            pass
    if prep:
        action.prep = prep
        if obj_msg_class.startswith('has_'):
            action.obj_msg_class = obj_msg_class[4:]
        else:
            action.obj_msg_class = 'rec_{0}'.format(obj_msg_class)
    for arg_name, value in kw_args.iteritems():
        setattr(action, arg_name, value)
    return action


def action_handler(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except PermError:
            self.display_line("You do not have permission to do that.")
        except ActionError as action_error:
            self.display_line(action_error.message, action_error.display)

    return wrapper


class ActionError(Exception):
    def __init__(self, message, display=None):
        self.message = message
        self.display = display


class _ActionObject(object):
    def __call__(self, **kwargs):
        return self.execute(**kwargs)

