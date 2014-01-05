class ProtoMeta(type):
    def __init__(cls, class_name, bases, new_attrs):
        cls._meta_init_attrs(new_attrs)

    def _meta_init_attrs(cls, new_attrs):
        for name, attr in new_attrs.iteritems():
            try:
                attr.meta_init(name)
            except AttributeError:
                pass


class RootProto(object):
    __metaclass__ = ProtoMeta
