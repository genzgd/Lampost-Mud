from lampost.context.resource import m_requires
from lampost.util.lmutil import find_extra

m_requires('log', 'mud_actions', __name__)

MISSING_VERB = "Unrecognized command '{verb}'.  Perhaps you should try 'help'?"
EXTRA_WORDS = "'{extra}' does not make sense with '{verb}'"
MISSING_TARGET = "'{command}' what? or whom?"
ABSENT_TARGET = "'{target}' is not here."
INVALID_TARGET = "You can't {verb} {target}."
INVALID_OBJECT = "You can't {verb} {target} {prep} {object}"
AMBIGUOUS_COMMAND = "Ambiguous command"


def has_action(entity, action, verb):
    return action in entity.actions.get(verb, []) or verb in mud_actions


class ActionMatch(object):
    def __init__(self, action, verb, args):
        self.action = action
        self.verb = verb
        self.args = args
        self.target = None
        self.obj = None
        self.target_method = None
        self.obj_method = None
        self.quantity = None
        self.obj_args = None

    @property
    def msg_class(self):
        return getattr(self.action, 'msg_class', None)

    @property
    def obj_msg_class(self):
        return getattr(self.action, 'obj_msg_class', None)

    @property
    def prep(self):
        return getattr(self.action, 'prep', None)

    @property
    def self_object(self):
        return hasattr(self.action, 'self_object')

    @property
    def item_action(self):
        return hasattr(self.action, 'item_action')

    @property
    def self_target(self):
        return hasattr(self.action, 'self_target')


def find_actions(entity, command):
    words = unicode(command).lower().split()
    matches = []
    for verb_size in range(1, len(words) + 1):
        verb = tuple(words[:verb_size])
        args = tuple(words[verb_size:])
        matches.extend([ActionMatch(action, verb, args) for action in entity.soul.get(verb, [])])
        matches.extend([ActionMatch(action, verb, args) for action in entity.actions.get(verb, [])])
        if verb in mud_actions:
            matches.append(ActionMatch(mud_actions[verb], verb, args))
    return matches


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
        raise ParseError(last_reason.format(**reject_format))

    def parse(self):
        self._reject(MISSING_VERB)
        self.find_targets()
        self.find_objects()
        self.validate_targets()
        self.validate_objects()
        if len(self._matches) > 1:
            raise ParseError(AMBIGUOUS_COMMAND)
        match = self._matches[0]
        return match.action, match.__dict__

    def find_targets(self):
        for match in reversed(self._matches):
            args, msg_class, prep = match.args, match.msg_class, match.prep
            if msg_class == 'no_args' and args:
                self._reject(EXTRA_WORDS, match)
                continue
            if not msg_class or msg_class == 'no_args':
                continue

            target_args = args
            if prep:
                try:
                    prep_loc = args.index(prep)
                    target_args = args[:prep_loc]
                    match.obj_args = args[(prep_loc + 1):]
                except ValueError:
                    if not match.self_object:
                        self._reject(MISSING_TARGET, match)
                        continue
            if msg_class == "rec_args":
                if not target_args:
                    self._reject(MISSING_TARGET, match)
            elif target_args:
                match.target = self._entity.target_key_map.get(target_args)
                if not match.target:
                    self._reject(ABSENT_TARGET, match)
            elif match.self_target:
                match.target = self._entity
            else:
                match.target = self._entity.env

    def find_objects(self):
        for match in reversed(self._matches):
            if match.obj_args:
                match.obj = self._entity.target_key_map.get(match.obj_args)
                if not match.obj:
                    self._reject(ABSENT_OBJECT, match)
            elif match.self_object:
                match.obj = self._entity

    def validate_targets(self):
        for match in reversed(self._matches):
            if match.target:
                match.target_method = getattr(match.target, match.msg_class, None)
                if match.target_method is None:
                    self._reject(INVALID_TARGET, match)
                elif match.item_action:
                    if match.target_method.im_self == match.target:
                        match.action = match.target_method
                    else:
                        self._reject(INVALID_TARGET, match)

    def validate_objects(self):
        for match in reversed(self._matches):
            if match.obj and match.obj_msg_class != "rec_args":
                match.obj_method = getattr(obj, action.obj_msg_class, None)
                if match.obj_method is None:
                    self._reject(INVALID_OBJECT, match)


def parse_actions(entity, command):
    return Parse(entity, command).parse()


class ParseError(Exception):
    def __init__(self, message):
        super(ParseError, self).__init__(message)
