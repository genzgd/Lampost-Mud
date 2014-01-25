import itertools
from lampost.context.resource import m_requires
from lampost.gameops.target import TargetClass
from lampost.util.lmutil import find_extra

m_requires('log', 'mud_actions', __name__)

MISSING_VERB = "Unrecognized command '{verb}'.  Perhaps you should try 'help'?"
EXTRA_WORDS = "'{extra}' does not make sense with '{verb}'"
MISSING_TARGET = "'{command}' what? or whom?"
ABSENT_TARGET = "'{target}' is not here."
INVALID_TARGET = "You can't {verb} {target}."
INVALID_OBJECT = "You can't {verb} {target} {prep} {object}"
INSUFFICIENT_QUANTITY = "Not enough there to {verb} {quantity}"
AMBIGUOUS_COMMAND = "Ambiguous command"


def has_action(entity, action, verb):
    return action in entity.actions.get(verb, []) or verb in mud_actions


class ActionMatch(object):
    target = None
    quantity = None
    prep = None

    def __init__(self, action, verb, args):
        self.action = action
        self.verb = verb
        self.args = args
        self.target_key = None
        self.target = None
        self.obj = None
        self.target_method = None
        self.obj_method = None
        self.obj_args = None


def find_actions(entity, command):
    words = unicode(command).lower().split()
    matches = []
    for verb_size in range(1, len(words) + 1):
        verb = tuple(words[:verb_size])
        args = tuple(words[verb_size:])
        matches.extend([ActionMatch(action, verb, args) for action in entity.soul.get(verb, [])])
        matches.extend([ActionMatch(action, verb, args) for action in entity.inven_actions.get(verb, [])])
        matches.extend([ActionMatch(action, verb, args) for action in entity.env.actions.get(verb, [])])
        if verb in mud_actions:
            matches.append(ActionMatch(mud_actions[verb], verb, args))
    return matches


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
            extra = find_extra(reject.verb, 0, self._command)
            reject_format['quantity'] = reject.quantity
            reject_format['verb'] = ' '.join(reject.verb)
            reject_format['extra'] = extra
            reject_format['prep'] = reject.prep
            if reject.prep:
                prep_ix = extra.find(reject.prep)
                if prep_ix == -1:
                    reject_format['target'] = extra
                else:
                    reject_format['target'] = extra[:prep_ix]
                reject_format['object'] = extra[prep_ix + len(reject.prep):]
            else:
                reject_format['target'] = extra
            if not reject_format['target'] and (last_reason == INVALID_TARGET or last_reason == ABSENT_TARGET):
                last_reason = MISSING_TARGET
        raise ParseError(last_reason.format(**reject_format))

    def parse(self):
        self._reject(MISSING_VERB)
        self.validate_syntax()
        self.validate_targets()
        #self.find_objects()
        #self.validate_objects()
        if len(self._matches) > 1:
            raise ParseError(AMBIGUOUS_COMMAND)
        match = self._matches[0]
        return match.action, match.__dict__

    def find_targets(self, target_key, target_class):
        return itertools.chain.from_iterable([target_type.target_finder(self._entity, target_key) for target_type in target_class])

    # noinspection PyUnboundLocalVariable
    @match_filter
    def validate_syntax(self, match):
        action = match.action
        target_class, args = action.target_class, match.args
        if not target_class:
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
                target_args = target_key[:prep_loc]
                match.obj_args = target_args[(prep_loc + 1):]
            except ValueError:
                if not hasattr(action, 'self_object'):
                    return MISSING_TARGET
        if target_key:
            try:
                target_index = int(target_key[-1]) - 1
                target_key = target_key[:-1]
            except ValueError:
                target_index = 0
        if target_key:
            targets = list(self.find_targets(target_key, target_class))
            try:
                match.target = targets[target_index]
            except IndexError:
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

    def find_objects(self):
        for match in reversed(self._matches):
            if match.obj_args:
                match.obj = self._entity.target_key_map.get(match.obj_args)
                if not match.obj:
                    self._reject(ABSENT_OBJECT, match)
            elif match.self_object:
                match.obj = self._entity

    def validate_objects(self):
        for match in reversed(self._matches):
            if match.obj and match.obj_msg_class != "rec_args":
                match.obj_method = getattr(obj, action.obj_msg_class, None)
                if match.obj_method is None:
                    self._reject(INVALID_OBJECT, match)


def parse_actions(entity, command):
    return Parse(entity, command).parse()


class ParseError(Exception):
    pass
