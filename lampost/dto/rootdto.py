from json import JSONEncoder

def get_dict(obj):
    raw = {}
    for key, value in obj.__dict__.iteritems():
        raw[key] = value
    return raw

class DTOEncoder(JSONEncoder):
    def default(self, o):
        try:
            return get_dict(o)
        except:
            return JSONEncoder.default(self, o)

class RootDTO():
    def __init__(self, **kw):
        self.merge_dict(kw)

    def append(self, prop_name, other):
        setattr(self, prop_name, get_dict(other))

    def merge(self, other):
        self.merge_dict(get_dict(other))
        return self

    def iteritems(self):
        return get_dict(self).iteritems()

    def merge_dict(self, dictionary):
        for key, value in dictionary.iteritems():
            peer = getattr(self, key, None)
            try:
                peer.extend(value)
            except:
                try:
                    peer.merge(value)
                except:
                    setattr(self, key, value)
        return self

    def get_json(self):
        return RootDTO.__encoder__.encode(self)

    __encoder__ = DTOEncoder()
    json = property(get_json)

