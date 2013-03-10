import re

from lampost.util.lmutil import pronouns

defaults = {'e':'s', 't':'e', 'st':'s', 'et':'e', 'sf':'s', 'ef':'e', 'sa':'st', 'ea':'et'}

broadcast_types = [{'id':'s', 'label':'To self (no target)', 'reduce':'s'},
                   {'id':'e', 'label':'To others (no target)', 'reduce':'s'},
                   {'id':'t', 'label':'To target (target is other)', 'reduce':'e'},
                   {'id':'st', 'label':'To self (target is other)', 'reduce':'s'},
                   {'id':'et', 'label':'To others (target is other)', 'reduce': 'e'},
                   {'id':'sf', 'label':'To self (target is self)', 'reduce':'s'},
                   {'id':'ef', 'label':'To others (target is self)', 'reduce': 'e'},
                   {'id':'sa', 'label':'To self (target is not living)', 'reduce':'st'},
                   {'id':'ea', 'label':'To environment (target is not living)', 'reduce':'et'}]

broadcast_tokens = [{'id':'n', 'token':'Subject name'},
                    {'id':'N', 'token':'Target name'},
                    {'id':'e', 'token':'Subject pronoun'},
                    {'id':'E', 'token':'Target pronoun'},
                    {'id':'s', 'token':'Subject possessive pronoun'},
                    {'id':'S', 'token':'Target possessive pronoun'},
                    {'id':'m', 'token':'Subject objective pronoun'},
                    {'id':'M', 'token':'Target objective pronoun'},
                    {'id':'f', 'token':'Subject self pronoun'},
                    {'id':'F', 'token':'Target self pronoun'}]

token_pattern = re.compile('\$([nNeEsSmMfF])')


class BroadcastMap(object):
    def __init__(self,  **kwargs):
        self.populate(kwargs)

    def populate(self, type_map):
        for key, value in type_map.iteritems():
            value = token_pattern.sub(r'{\1}', value)
            setattr(self, key, value)

    def __getitem__(self, msg_key):
        while True:
            msg = getattr(self, msg_key, None)
            if msg:
                return msg
            msg_key = defaults[msg_key]
            if not msg_key:
                return "Invalid message type"


class Broadcast(object):
    def __init__(self, broadcast_map=None, source=None, target=None, color=0x000000, silent=False, **kwargs):
        if broadcast_map:
            self.broadcast_map = broadcast_map
        else:
            self.broadcast_map = BroadcastMap(**kwargs)
        self.source = source
        self.target = target
        self.color = color
        self.silent = silent

    def translate(self, observer):
        if self.silent and observer == self.source:
            return None
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
        if getattr(self.target, 'living'):
            if self.source == observer:
                return self.substitute('st')
            return self.substitute('et')
        if self.source == observer:
            return self.substitute('sa')
        return self.substitute('ea')

    def substitute(self, version):
        message = self.broadcast_map[version]
        if self.source:
            s_name = self.source.name
            s_sub, s_obj, s_poss, s_self = pronouns[getattr(self.source, 'sex', 'none')]
        else:
            s_name = s_sub = s_obj = s_poss = s_self = None
        if self.target:
            t_name = self.target.name
            t_sub, t_obj, t_poss, t_self = pronouns[getattr(self.target, 'sex', 'none')]
        else:
            t_name = t_sub = t_obj = t_poss = t_self = None

        result = message.format(n=s_name, N=t_name, e=s_sub, E=t_sub,
                                s=s_poss, S=t_poss, m=s_obj, M=t_obj, f=s_self, F=t_self)
        if result:
            result = "{0}{1}".format(result[0], result[1:])
        return result


class SingleBroadcast():
    def __init__(self, all_msg, color=0x00000):
        self.all_msg = all_msg
        self.color = color

    def translate(self, ignored):
        return self.all_msg
