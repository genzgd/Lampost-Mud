import itertools

from lampost.gameops import target_gen
from lampost.context.resource import m_requires
from lampost.gameops.action import find_actions
from lampost.util.lputil import find_extra, ClientError

m_requires(__name__, 'log', 'mud_actions')

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
    actions = {action for action in itertools.chain.from_iterable(
        actions.get(verb, []) for actions in (entity.soul, entity.inven_actions))}
    try:
        actions.add(mud_actions[verb])
    except KeyError:
        pass
    actions.update(find_actions(verb, entity.env.action_providers))
    return actions


def has_action(entity, action, verb):
    return action in all_actions(entity, verb)


def entity_actions(entity, command):
    words = command.lower().split()
    matches = []
    for verb_size in range(1, len(words) + 1):
        verb = tuple(words[:verb_size])
        args = tuple(words[verb_size:])
        matches.extend([ActionMatch(action, verb, args) for action in all_actions(entity, verb)])
    return matches


def find_targets(entity, target_key, target_class, action=None):
    return itertools.chain.from_iterable([target_func(target_key, entity, action) for target_func in target_class])


class ActionMatch():
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
    except (TypeError, IndexError):
        pass
    except ValueError:
        try:
            first_split = target_key[0].split('.')
            return int(first_split[0]) - 1, (first_split[1],) + target_key[1:]
        except (ValueError, IndexError):
            pass
    return 0, target_key


class Parse():
    def __init__(self, entity, command):
        matches = entity_actions(entity, command)
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
            if extra:
                extra = extra.strip()
            reject_format['quantity'] = reject.quantity
            reject_format['verb'] = ' '.join(reject.verb)
            reject_format['extra'] = extra
            reject_format['prep'] = reject.prep
            if extra and reject.prep:
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
                    try:
                        last_reason = reject.action.target_class[0].absent_msg
                    except (IndexError, AttributeError):
                        pass
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
        target_class = getattr(action, 'target_class', None)
        if not target_class:
            return
        if target_class == 'no_args':
            return EXTRA_WORDS if match.args else None
        target_key = match.args
        if hasattr(action, 'quantity'):
            try:
                match.quantity = int(match.args[0])
                target_key = match.args[1:]
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
        if target_class == 'args':
            match.target = target_key
            return
        target_index, target_key = capture_index(target_key)
        if target_key:
            targets = find_targets(self._entity, target_key, target_class, action)
            try:
                target = next(itertools.islice(targets, target_index, target_index + 1))
            except StopIteration:
                return ABSENT_TARGET
        elif hasattr(action, 'self_target'):
            target = self._entity
        elif target_gen.env in target_class:
            target = self._entity.env
        else:
            return MISSING_TARGET
        if match.quantity and match.quantity > getattr(target, 'quantity', 0):
            return INSUFFICIENT_QUANTITY
        msg_class = getattr(match.action, 'msg_class', None)
        if msg_class:
            match.target_method = getattr(target, msg_class, None)
            if match.target_method is None:
                return INVALID_TARGET
        match.target = target

    @match_filter
    def parse_objects(self, match):
        obj_target_class = getattr(match.action, 'obj_target_class', None)
        if not obj_target_class:
            return
        if obj_target_class == 'args':
            match.obj = match.obj_key
            return
        obj_index, obj_key = capture_index(match.obj_key)
        if obj_key:
            objects = find_targets(self._entity, obj_key, obj_target_class)
            try:
                obj = next(itertools.islice(objects, obj_index, obj_index + 1))
            except StopIteration:
                return ABSENT_OBJECT
        elif hasattr(match.action, 'self_object'):
            obj = self._entity
        else:
            return MISSING_TARGET

        obj_msg_class = getattr(match.action, 'obj_msg_class', None)
        if obj_msg_class:
            match.obj_method = getattr(obj, obj_msg_class, None)
            if match.obj_method is None:
                return INVALID_OBJECT
        match.obj = obj


def parse_actions(entity, command):
    return Parse(entity, command).parse()


def parse_chat(verb, command):
    verb_str = " ".join(verb)
    verb_ix = command.lower().index(verb_str) + len(verb_str)
    return command[verb_ix:].strip()


class ParseError(ClientError):
    pass
