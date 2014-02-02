import sys

from collections import defaultdict

_dbo_registry = {}
_subclass_registry = defaultdict(list)


def set_dbo_class(class_id, dbo_class):
    if isinstance(class_id, basestring):
        _dbo_registry[class_id] = dbo_class


def get_dbo_class(class_id):
    try:
        return _dbo_registry[class_id]
    except KeyError:
        sys.stderr.write("ERROR: No class found in registry for dbo class id: {}\n".format(class_id))


def add_sub_class(cls):
    if cls.dbo_key_type:
        _subclass_registry[cls.dbo_key_type].append(cls.sub_class_id)
    else:
        _subclass_registry[cls.class_id].append(cls.sub_class_id)

def get_sub_classes(class_id):
    return _subclass_registry.get(class_id, [])



