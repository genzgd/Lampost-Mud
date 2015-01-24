import re

from lampost.util.lputil import pronouns

defaults = {'e': 's', 't': 'e', 'st': 's', 'et': 'e', 'sf': 's', 'ef': 'e', 'sa': 'st', 'ea': 'et'}

broadcast_types = [{'id': bt[0], 'label': bt[1], 'reduce': bt[2], 'grid_x': bt[3], 'grid_y': bt[4]} for bt in [
    ('s', 'To self (no target)', 's', 0, 0),
    ('e', 'To others (no target)', 's', 0, 1),
    ('t', 'To target (target is other)', 'e', 0, 2),
    ('st', 'To self (target is other)', 's', 1, 0),
    ('et', 'To others (target is other)', 'e', 1, 1),
    ('sf', 'To self (target is self)', 's', 2, 0),
    ('ef', 'To others (target is self)', 'e', 2, 1),
    ('sa', 'To self (target is not living)', 'st', 3, 0),
    ('ea', 'To environment (target is not living)', 'et', 3, 1)]]

broadcast_tokens = [{'id': token_id, 'token': token} for token_id, token in [
    ('n', 'Subject name'),
    ('N', 'Target name'),
    ('e', 'Subject pronoun'),
    ('E', 'Target pronoun'),
    ('s', 'Subject possessive pronoun'),
    ('S', 'Target possessive pronoun'),
    ('m', 'Subject objective pronoun'),
    ('M', 'Target objective pronoun'),
    ('f', 'Subject self pronoun'),
    ('F', 'Target self pronoun'),
    ('a', 'Absolute possessive subj'),
    ('A', 'Absolute possessive targ'),
    ('v', 'Action/verb')]]

token_pattern = re.compile('\$([nNeEsSmMfFaA])')


def substitute(message, source=None, target=None, verb=None, **ext_fmt):
    if source:
        s_name = getattr(source, 'name', source)
        s_sub, s_obj, s_poss, s_self, s_abs = pronouns[getattr(source, 'sex', 'none')]
    else:
        s_name = s_sub = s_obj = s_poss = s_self = s_abs = None
    if target:
        t_name = getattr(target, 'name', target)
        t_sub, t_obj, t_poss, t_self, t_abs = pronouns[getattr(target, 'sex', 'none')]
    else:
        t_name = t_sub = t_obj = t_poss = t_self = t_abs = None

    result = message.format(n=s_name, N=t_name, e=s_sub, E=t_sub, s=s_poss, S=t_poss,
                            m=s_obj, M=t_obj, f=s_self, F=t_self, a=s_abs, A=t_abs,
                            v=verb, **ext_fmt)
    return result


class BroadcastMap():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            value = token_pattern.sub(r'{\1}', value)
            setattr(self, key, value)

    def __getitem__(self, msg_key):
        while True:
            msg = getattr(self, msg_key, None)
            if msg:
                return msg
            msg_key = defaults.get(msg_key, None)
            if not msg_key:
                return "[EMPTY]"


class Broadcast():
    def __init__(self, broadcast_map=None, source=None, target=None, display='default',
                 silent=False, verb=None, ext_fmt=None, **kwargs):
        if broadcast_map:
            self.broadcast_map = broadcast_map
        else:
            self.broadcast_map = BroadcastMap(**kwargs)
        self.source = source
        self.target = target
        self.display = display
        self.silent = silent
        self.verb = verb
        self.ext_fmt = ext_fmt if ext_fmt else {}

    def translate(self, observer):
        if self.silent and observer == self.source:
            return None
        if hasattr(self.broadcast_map, 'raw'):
            return self.broadcast_map['raw']
        if not self.target:
            if not self.source or self.source == observer:
                return self.substitute('s')
        if self.target == self.source:
            if self.source == observer:
                return self.substitute('sf')
            return self.substitute('ef')
        if self.target == observer:
            return self.substitute('t')
        if not self.target:
            return self.substitute('e')
        if getattr(self.target, 'living', False):
            if self.source == observer:
                return self.substitute('st')
            return self.substitute('et')
        if self.source == observer:
            return self.substitute('sa')
        return self.substitute('ea')

    def substitute(self, version):
        return substitute(self.broadcast_map[version], self.source, self.target, self.verb, **self.ext_fmt)
