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
        actions += [(action, verb, args) for action in entity.soul.get(verb, [])]
        actions += [(action, verb, args) for action in entity.actions.get(verb, [])]
        actions += [(action, verb, args) for action in mud_actions.verb_list(verb)]
    return actions


def parse_actions(entity, actions):
    if not actions:
        raise ParseError(MISSING_VERB, "What?")
    matches = find_targets(entity, actions)
    if not matches:
        raise ParseError(MISSING_TARGET, "You can't do that.")
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
                prep_loc = args.index(action.prep)
                target_args = args[:prep_loc]
                obj_args = args[(prep_loc + 1):]
            except ValueError:
                if not hasattr(action, 'self_object'):
                    continue
        if msg_class == "rec_args":
            if target_args:
                target_matches.append((action, verb, args, target_args, obj_args))
        elif target_args:
            target = entity.target_key_map.get(target_args)
            if target:
                target_matches.append((action, verb, args, target, obj_args))
        elif hasattr(action, 'self_target'):
            target_matches.append((action, verb, args, entity, obj_args))
        else:
            target_matches.append((action, verb, args, entity.env, obj_args))
    return target_matches


def find_objects(entity, matches):
    object_matches = []
    for action, verb, args, target, obj_args in matches:
        if getattr(action, 'obj_msg_class', None) == "rec_args":
            object_matches.append((action, verb, args, target, obj_args))
        elif obj_args:
            obj = entity.target_key_map.get(obj_args)
            if obj:
                object_matches.append((action, verb, args, target, obj))
        elif hasattr(action, 'self_object'):
            object_matches.append((action, verb, args, target, entity))
        else:
            object_matches.append((action, verb, args, target, None))
    return object_matches


def validate_targets(matches):
    target_matches = []
    for action, verb, args, target, obj in matches:
        if getattr(action, 'msg_class', None) == 'rec_args':
            target_matches.append((action, verb, args, target, obj, None))
        elif target:
            target_method = getattr(target, action.msg_class, None)
            if target_method:
                if hasattr(action, 'item_action'):
                    if target_method.im_self == target:
                        target_matches.append((target_method, verb, args, target, obj, target_method))
                else:
                    target_matches.append((action, verb, args, target, obj, target_method))
        else:
            target_matches.append((action, verb, args, None, None, None))
    return target_matches


def validate_objects(matches):
    object_matches = []
    for action, verb, args, target, obj, target_method in matches:
        if not obj or action.obj_msg_class == "rec_args":
            object_matches.append((action, verb, args, target, obj, target_method, None))
        else:
            obj_method = getattr(obj, action.obj_msg_class, None)
            if obj_method:
                object_matches.append((action, verb, args, target, obj, target_method, obj_method))
    return object_matches


class ParseError(Exception):
    def __init__(self, error_code, message):
        super(ParseError, self).__init__(message)
        self.error_code = error_code
