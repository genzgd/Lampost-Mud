import itertools
from lampost.context.resource import m_requires
from lampost.gameops.target import TargetClass
from lampost.util.lmutil import find_extra

m_requires('log', 'mud_actions', __name__)

MISSING_VERB = "Unrecognized command '{verb}'.  Perhaps you should try 'help'?"
EXTRA_WORDS = "'{extra}' does not make sense with '{verb}'"
MISSING_TARGET = "'{command}' what? or whom?"
ABSENT_TARGET = "'{target}' is not here."
ABSENT_OBJECT = "'{object}' is not here."
INVALID_TARGET = "You can't {verb} {target}."
INVALID_OBJECT = "You can't {verb} {target} {prep} {object}"
INSUFFICIENT_QUANTITY = "Not enough there to {verb} {quantity}"
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
        for match in self._matches:
            result = func(self, match)
            if result:
                self._reject(result, match)
    return wrapper


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
            if not reject_format['target'] and (last_reason == INVALID_TARGET or last_reason == ABSENT_TARGET):
                last_reason = MISSING_TARGET
        raise ParseError(last_reason.format(**reject_format))

    # noinspection PyArgumentList
    def parse(self):
        self._reject(MISSING_VERB)
        self.validate_syntax()
        self.validate_targets()
        self.find_objects()
        self.validate_objects()
        if len(self._matches) > 1:
            raise ParseError(AMBIGUOUS_COMMAND)
        match = self._matches[0]
        return match.action, match.__dict__

    def find_targets(self, target_key, target_class):
        return itertools.chain.from_iterable([target_type.target_finder(self._entity, target_key) for target_type in target_class])

    @match_filter
    def validate_syntax(self, match):
        action = match.action
        target_class, args = action.target_class, match.args
        if not target_class:
            return EXTRA_WORDS if args else None
        if target_class == TargetClass.ARGS:
            return
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
                    return MISSING_TARGET
        target_index = 0
        if target_key:
            try:
                target_index = int(target_key[-1]) - 1
                target_key = target_key[:-1]
            except ValueError:
                pass
        if target_key:
            targets = self.find_targets(target_key, target_class)
            try:
                match.target = itertools.islice(targets, target_index, target_index + 1).next()
            except StopIteration:
                return ABSENT_TARGET
        else:
            if hasattr(action, 'self_target'):
                match.target = self._entity
            elif TargetClass.ENV in target_class:
                match.target = self._entity.env
            else:
                return MISSING_TARGET

    @match_filter
    def validate_targets(self, match):
        target = match.target
        if not target:
            return
        if match.quantity and match.quantity < getattr(target, 'quantity', 0):
            return INSUFFICIENT_QUANTITY
        match.target_method = getattr(target, match.action.msg_class, None)
        if match.target_method is None:
            return INVALID_TARGET
        if hasattr(match.action, 'item_action'):
            if match.target_method.im_self == target:
                match.action = match.target_method
            else:
                return INVALID_TARGET

    @match_filter
    def find_objects(self, match):
        obj_target_class, obj_key = getattr(match.action, 'obj_target_class', None), match.obj_key
        if not obj_target_class or obj_target_class == TargetClass.ARGS:
            return
        obj_index = 0
        if obj_key:
            try:
                obj_index = int(obj_key[-1]) - 1
                obj_key = obj_key[:-1]
            except ValueError:
                pass
        if obj_key:
            objects = self.find_targets(obj_key, obj_target_class)
            try:
                match.obj = itertools.islice(objects, obj_index, obj_index + 1).next()
            except StopIteration:
                return ABSENT_OBJECT
        else:
            if hasattr(match.action, 'self_obj'):
                match.obj = self._entity
            else:
                return MISSING_OBJECT

    @match_filter
    def validate_objects(self, match):
        obj_msg_class = getattr(match.action, 'obj_msg_class', None)
        if match.obj and obj_msg_cls:
            match.obj_method = getattr(obj, obj_msg_class, None)
            if match.obj_method is None:
                return INVALID_OBJECT


def parse_actions(entity, command):
    return Parse(entity, command).parse()


class ParseError(Exception):
    pass
