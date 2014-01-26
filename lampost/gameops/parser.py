import itertools

from lampost.context.resource import m_requires
from lampost.gameops.target import TargetClass
from lampost.util.lmutil import find_extra

m_requires('log', 'mud_actions', __name__)

MISSING_VERB = "Unrecognized command '{verb}'.  Perhaps you should try 'help'?"
EXTRA_WORDS = "'{extra}' does not make sense with '{verb}'."
MISSING_TARGET = "'{command}' what? or whom?"
ABSENT_TARGET = "'{target}' is not here."
ABSENT_OBJECT = "'{object}' is not here."
MISSING_PREP = "'{prep}' missing from command."
INVALID_TARGET = "You can't {verb} {target}."
INVALID_OBJECT = "You can't {verb} {target} {prep} {object}."
INSUFFICIENT_QUANTITY = "Not enough there to {verb} {quantity}."
AMBIGUOUS_COMMAND = "Ambiguous command"


def all_actions(entity, verb):
    actions = [action for action in itertools.chain.from_iterable(
        [actions.get(verb, []) for actions in (entity.soul, entity.inven_actions, entity.env.actions)])]
    if verb in mud_actions:
        actions.append(mud_actions[verb])
    return actions


def has_action(entity, action, verb):
    return action in all_actions(entity, verb)


def find_actions(entity, command):
    words = unicode(command).lower().split()
    matches = []
    for verb_size in range(1, len(words) + 1):
        verb = tuple(words[:verb_size])
        args = tuple(words[verb_size:])
        matches.extend([ActionMatch(action, verb, args) for action in all_actions(entity, verb)])
    return matches


def find_targets(entity, target_key, target_class):
    return itertools.chain.from_iterable([target_type.target_finder(entity, target_key) for target_type in target_class])


class ActionMatch(object):
    target = None
    quantity = None
    prep = None
    obj_key = None
    target_key = None
    obj = None
    target_method = None
    obj_method = None

    def __init__(self, action, verb, args):
        self.action = action
        self.verb = verb
        self.args = args


def match_filter(func):
    def wrapper(self):
        for match in reversed(self._matches):
            result = func(self, match)
            if result:
                self._reject(result, match)
    return wrapper


def capture_index(target_key):
    try:
        return int(target_key[-1]) - 1, target_key[:-1]
    except IndexError:
        pass
    except ValueError:
        try:
            first_split = target_key[0].split('.')
            return int(first_split[0]) - 1, (first_split[1],) + target_key[1:]
        except (ValueError, IndexError):
            pass
    return 0, target_key


class Parse(object):
    def __init__(self, entity, command):
        matches = find_actions(entity, command)
        matches = entity.filter_actions(matches)
        self._entity = entity
        self._matches = matches
        self._command = command

    def _reject(self, last_reason, reject=None):
        if reject:
            self._matches.remove(reject)
        if self._matches:
            return
        reject_format = {'command': self._command, 'verb': self._command.split(' ')[0]}
        if reject:
            extra = find_extra(reject.verb, 0, self._command).strip()
            reject_format['quantity'] = reject.quantity
            reject_format['verb'] = ' '.join(reject.verb)
            reject_format['extra'] = extra
            reject_format['prep'] = reject.prep
            if reject.prep:
                prep_ix = extra.find(reject.prep)
                if prep_ix == -1:
                    reject_format['target'] = extra
                else:
                    reject_format['target'] = extra[:prep_ix].strip()
                reject_format['object'] = extra[prep_ix + len(reject.prep):]
            else:
                reject_format['target'] = extra
            if last_reason in (INVALID_TARGET, ABSENT_TARGET):
                if not reject_format['target']:
                    last_reason = MISSING_TARGET
                elif last_reason == ABSENT_TARGET:
                    last_reason = reject.action.target_class[0].absent_msg
        raise ParseError(last_reason.format(**reject_format))

    # noinspection PyArgumentList
    def parse(self):
        self._reject(MISSING_VERB)
        self.parse_targets()
        self.parse_objects()
        if len(self._matches) > 1:
            raise ParseError(AMBIGUOUS_COMMAND)
        match = self._matches[0]
        return match.action, match.__dict__


    @match_filter
    def parse_targets(self, match):
        action = match.action
        target_class, args = action.target_class, match.args
        if not target_class:
            return
        if target_class == TargetClass.NO_ARGS:
            return EXTRA_WORDS if args else None
        target_key = args
        if hasattr(action, 'quantity'):
            try:
                match.quantity = int(args[0])
                target_key = args[1:]
            except ValueError:
                pass
        match.prep = getattr(action, 'prep', None)
        if match.prep:
            try:
                prep_loc = target_key.index(match.prep)
                match.obj_key = target_key[(prep_loc + 1):]
                target_key = target_key[:prep_loc]
            except ValueError:
                if not hasattr(action, 'self_object'):
                    return MISSING_PREP
        target_index, target_key = capture_index(target_key)
        if TargetClass.ARGS in target_class:
            match.target = target_key
            return
        if target_key:
            targets = find_targets(self._entity, target_key, target_class)
            try:
                target = itertools.islice(targets, target_index, target_index + 1).next()
            except StopIteration:
                return ABSENT_TARGET
        else:
            if hasattr(action, 'self_target'):
                target = self._entity
            elif TargetClass.ENV in target_class:
                target = self._entity.env
            else:
                return MISSING_TARGET
        if match.quantity and match.quantity > getattr(target, 'quantity', 0):
            return INSUFFICIENT_QUANTITY
        match.target_method = getattr(target, match.action.msg_class, None)
        if match.target_method is None:
            return INVALID_TARGET
        if hasattr(match.action, 'item_action'):
            if match.target_method.im_self == target:
                match.action = match.target_method
            else:
                return INVALID_TARGET
        match.target = target

    @match_filter
    def parse_objects(self, match):
        obj_target_class, obj_key = getattr(match.action, 'obj_target_class', None), match.obj_key
        if not obj_target_class:
            return
        if TargetClass.ARGS in obj_target_class:
            match.obj = match.obj_key
            return
        obj_index, obj_key = capture_index(match.obj_key)
        if obj_key:
            objects = find_targets(self._entity, obj_key, obj_target_class)
            try:
                obj = itertools.islice(objects, obj_index, obj_index + 1).next()
            except StopIteration:
                return ABSENT_OBJECT
        else:
            if hasattr(match.action, 'self_obj'):
                obj = self._entity
            else:
                return MISSING_OBJECT

        obj_msg_class = getattr(match.action, 'obj_msg_class', None)
        if obj_msg_class:
            match.obj_method = getattr(obj, obj_msg_class, None)
            if match.obj_method is None:
                return INVALID_OBJECT
        match.obj = obj


def parse_actions(entity, command):
    return Parse(entity, command).parse()


class ParseError(Exception):
    pass
