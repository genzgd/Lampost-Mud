import inspect

import itertools

from lampost.context.resource import m_requires
from lampost.core.auto import AutoField
from lampost.core.meta import CoreMeta
from lampost.gameops import target_gen
from lampost.util.lputil import ClientError

m_requires(__name__, 'log')


def convert_verbs(verbs):
    results = set()

    def add_verb(verb):
        results.add(tuple(verb.split(' ')))
    try:
        add_verb(verbs)
    except AttributeError:
        for verb in verbs:
            add_verb(verb)
    return results


def make_action(action, verbs=None, msg_class=None, target_class=None, prep=None,
                obj_msg_class=None, obj_target_class=None, **kw_args):
    if verbs:
        action.verbs = getattr(action, 'verbs', set())
        action.verbs.update(convert_verbs(verbs))

    if msg_class:
        action.msg_class = msg_class

    if target_class:
        action.target_class = target_gen.make(target_class)
    elif not hasattr(action, 'target_class'):
        try:
            args, var_args, var_kwargs, defaults = inspect.getargspec(action)
        except TypeError:
            args, var_args, var_kwargs, defaults = inspect.getargspec(action.__call__)
        target_args = len(args) - len([arg for arg in args if arg in {'self', 'source', 'command', 'args', 'verb'}])
        if target_args:
            action.target_class = target_gen.defaults
        elif not args or len(args) == 1 and args[0] == 'source':
            action.target_class = 'no_args'

    if prep:
        action.prep = prep
        if obj_target_class:
            action.obj_target_class = target_gen.make(obj_target_class)
        elif not hasattr(action, 'obj_target_class'):
            action.obj_target_class = target_gen.defaults
        if obj_msg_class:
            action.obj_msg_class = obj_msg_class
    for arg_name, value in kw_args.items():
        setattr(action, arg_name, value)
    return action


def obj_action(**kwargs):

    def decorator(func):
        if 'verbs' not in kwargs:
            kwargs['verbs'] = func.__name__
        if 'target_class' not in kwargs:
            kwargs['target_class'] = 'func_owner'
        make_action(func, **kwargs)
        return func
    return decorator


def add_action(action_set, action):
    for verb in getattr(action, "verbs", []):
        action_set[verb].add(action)
    for sub_action in getattr(action, "action_providers", []):
        add_action(action_set, sub_action)


def add_actions(action_set, actions):
    for action in actions:
        add_action(action_set, action)


def remove_action(action_set, action):
    for verb in getattr(action, 'verbs', []):
        verb_set = action_set.get(verb, None)
        if verb_set:
            verb_set.remove(action)
            if not verb_set:
                del action_set[verb]
        else:
            debug("Trying to remove non-existent action {}", verb)
    for sub_action in getattr(action, 'action_providers', ()):
        remove_action(action_set, sub_action)


def find_actions(verb, action_set):
    for action in action_set:
        try:
            if verb in action.verbs:
                yield action
        except AttributeError:
            pass
        for sub_action in find_actions(verb, getattr(action, 'action_providers', [])):
            yield sub_action


def remove_actions(action_set, actions):
    for action in actions:
        remove_action(action_set, action)


def action_handler(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except ClientError as client_error:
            self.display_line(client_error.client_message, client_error.display)
    return wrapper


class ActionError(ClientError):
    def __init__(self, msg=None, display=None):
        super().__init__(msg, display)


class ActionProvider(metaclass=CoreMeta):
    instance_providers = AutoField([])

    @classmethod
    def _mixin_init(cls, name, bases, new_attrs):
        cls._update_set(bases, 'class_providers')
        cls.class_providers.update({func.__name__ for func in new_attrs.values() if hasattr(func, 'verbs')})

    @property
    def action_providers(self):
        return itertools.chain((getattr(self, func_name) for func_name in self.class_providers), self.instance_providers)
