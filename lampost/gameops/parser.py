from lampost.context.resource import m_requires

m_requires('log', 'mud_actions', __name__)

MISSING_VERB = 1
MISSING_TARGET = 2
MISSING_OBJECT = 3
INVALID_TARGET = 4
INVALID_OBJECT = 5
AMBIGUOUS = 6


def find_actions(entity, command):
    words = unicode(command).lower().split()
    actions = []
    for verb_size in range(1, len(words) + 1):
        verb = tuple(words[:verb_size])
        args = tuple(words[verb_size:])
        actions += [(action, verb, args) for action in entity.actions.get(verb, [])]
        actions += [(action, verb, args) for action in mud_actions.verb_list(verb)]
    return actions


def parse_actions(entity, actions):
    if not actions:
        raise ParseError(MISSING_VERB, "What?")
    matches = find_targets(entity, actions)
    if not matches:
        raise ParseError(MISSING_TARGET, "That is not here.")
    matches = find_objects(entity, matches)
    if not matches:
        raise ParseError(MISSING_OBJECT, "Incomplete command.")
    matches = validate_targets(matches)
    if not matches:
        raise ParseError(INVALID_TARGET, "You can't do that to that")
    matches = list(validate_objects(matches))
    if not matches:
        raise ParseError(INVALID_OBJECT, "You can't do that with that.")
    if len(matches) > 1:
        raise ParseError(AMBIGUOUS, "Ambiguous command.")
    match = matches[0]
    return match[0], {'verb': match[1], 'args': match[2], 'target': match[3], 'obj': match[4],
                      'target_method': match[5], 'obj_method': match[6]}


def has_action(entity, action, verb):
    return action in entity.actions.get(verb, []) or action in mud_actions.verb_list(verb)


def find_targets(entity, matches):
    target_matches = []
    for action, verb, args in matches:
        msg_class = getattr(action, 'msg_class', None)
        if msg_class == 'no_args' and args:
            continue
        if not msg_class or msg_class == 'no_args':
            target_matches.append((action, verb, args, None, None))
            continue
        target_args = args
        obj_args = None
        prep = getattr(action, 'prep', None)
        if prep:
            try:
                target_args = args[:args.index(action.prep)]
                obj_args = args[(prep_loc + 1):]
            except ValueError:
                continue
        if target_args:
            fixed_targets = getattr(action, "fixed_targets", None)
            target = entity.target_key_map.get(target_args)
            if target and (not fixed_targets or target in fixed_targets):
                target_matches.append((action, verb, args, target, obj_args))
        else:
            if getattr(action, 'self_default', None):
                target_matches.append((action, verb, args, entity, obj_args))
            else:
                target_matches.append((action, verb, args, entity.env, obj_args))
    return target_matches


def find_objects(entity, matches):
    object_matches = []
    for action, verb, args, target, obj_args in matches:
        if obj_args:
            object_matches += [(action, verb, args, target, obj) for obj in entity.target_key_map.get(obj_args, [])]
        else:
            object_matches.append((action, verb, args, target, None))
    return object_matches


def validate_targets(matches):
    target_matches = []
    for action, verb, args, target, obj in matches:
        if target:
            try:
                target_matches.append((action, verb, args, target, obj, getattr(target, action.msg_class)))
            except AttributeError:
                pass
        else:
            target_matches.append((action, verb, args, None, None, None))
    return target_matches


def validate_objects(matches):
    object_matches = []
    for action, verb, args, target, obj, target_method in matches:
        if obj:
            try:
                object_matches.append((action, verb, args, target, obj, target_method, getattr(obj, action.obj_msg_class)))
            except AttributeError:
                pass
        else:
            object_matches.append((action, verb, args, target, obj, target_method, None))
    return object_matches


class ParseError(Exception):
    def __init__(self, error_code, message):
        super(ParseError, self).__init__(message)
        self.error_code = error_code