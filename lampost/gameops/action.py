import inspect

from lampost.gameops import target_gen
from lampost.context.resource import m_requires
from lampost.util.lmutil import PermError, ClientError

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
        action.target_class = target_gen.defaults
        try:
            args, var_args, var_kwargs, defaults = inspect.getargspec(action)
        except TypeError:
            args, var_args, var_kwargs, defaults = inspect.getargspec(action.__call__)
        target_args = len(args) - len([arg for arg in args if arg in {'self', 'source', 'command', 'args', 'verb'}])
        if not target_args:
            if not args or len(args) == 1 and args[0] == 'source':
                action.target_class = 'no_args'
            else:
                action.target_class = None

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


def item_action(**kwargs):
    local_args = kwargs

    def decorator(func):
        verbs = local_args.get('verbs', None)
        msg_class = local_args.get('msg_class', None)
        if not verbs:
            verbs = func.__name__
        if not msg_class:
            msg_class = verbs
            func.self_action = True
        local_args['verbs'] = verbs
        local_args['msg_class'] = msg_class
        make_action(func, **local_args)
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
            debug("Trying to remove non-existent action {}".format(verb))


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
    pass

