from lampost.util.lmutil import pronouns
defaults = {'e':'s', 't':'e', 'st':'s', 'et':'e', 'sf':'s', 'ef':'e'}

class BroadcastMap(object):
    def __init__(self, def_msg=None, **kwargs):
        self.s = def_msg
        for key, value in kwargs.iteritems():
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
        if self.source == observer:
            return self.substitute('st')
        return self.substitute('et')

    def substitute(self, version):
        message = self.broadcast_map[version]
        if self.source:
            s_name = self.source.name
            s_sub, s_obj, s_poss, s_self = pronouns(getattr(self.source, 'sex', None))
        else:
            s_name = s_sub = s_obj = s_poss = s_self = None
        if self.target:
            t_name = self.target.name
            t_sub, t_obj, t_poss, t_self = pronouns(self.target.sex)
        else:
            t_name = t_sub = t_obj = t_poss = t_self = None

        result =  message.format(n=s_name, N=t_name, e=s_sub, E=t_sub,
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
