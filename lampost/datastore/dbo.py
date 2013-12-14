from lampost.context.resource import m_requires
from lampost.util.lmutil import cls_name

m_requires('log', 'datastore', 'encode', 'cls_registry', __name__)


class RootDBOMeta(type):

    def __init__(cls, class_name, bases, new_attrs):
        if "RootDBO" in [base.__name__ for base in bases]:
            cls.dbo_base_class = cls

        def build_coll(coll_name):
            coll = set()
            for base in bases:
                coll.update(base.__dict__.get(coll_name, ()))
            coll.update(new_attrs.get(coll_name, ()))
            setattr(cls, coll_name, coll)

        build_coll('dbo_fields')
        build_coll('dbo_maps')
        build_coll('dbo_lists')
        build_coll('dbo_refs')


class RootDBO(object):
    __metaclass__ = RootDBOMeta
    dbo_key_type = None
    dbo_set_key = None

    dbo_indexes = ()

    def __init__(self, dbo_id=None):
        if dbo_id:
            self.dbo_id = unicode(str(dbo_id).lower())

    def append_list(self, attr_name, value):
        try:
            self.__dict__[attr_name].append(value)
        except KeyError:
            new_list = list()
            setattr(self, attr_name, new_list)
            new_list.append(value)

    def remove_list(self, attr_name, value):
        my_list = getattr(self, attr_name)
        my_list.remove(value)
        if not my_list:
            self.__dict__.pop(attr_name, None)

    def append_map(self, attr_name, value, map_key=None):
        if not map_key:
            map_key = value.dbo_id
        try:
            self.__dict__[attr_name][map_key] = value
        except KeyError:
            new_map = dict()
            setattr(self, attr_name, new_map)
            new_map[map_key] = value

    def remove_map(self, attr_name, value):
        my_map = getattr(self, attr_name)
        my_map.pop(value.dbo_id, None)
        if not my_map:
            self.__dict__.pop(attr_name, None)

    def del_coll(self, attr_name):
        self.__dict__.pop(attr_name, None)

    def on_loaded(self):
        pass

    @property
    def dbo_key(self):
        return unicode(":".join([self.dbo_key_type, self.dbo_id]))

    @property
    def dbo_debug_key(self):
        if self.dbo_key_type:
            return self.dbo_key
        return '-embedded-'

    @property
    def save_dbo_dict(self):
        return to_dbo_dict(self, True)

    @property
    def dbo_dict(self):
        return to_dbo_dict(self)

    @property
    def dto_value(self):
        dbo_dict = to_dbo_dict(self)
        dbo_dict['dbo_id'] = self.dbo_id
        dbo_dict['dbo_key_type'] = self.dbo_key_type
        return dbo_dict

    @property
    def json(self):
        return json_encode(to_dbo_dict(self))

    def autosave(self):
        save_object(self, autosave=True)

    def rec_describe(self):
        return dbo_describe(self)


def dbo_describe(dbo, level=0, follow_refs=True, dict_key=None):
    display = []

    def append(key, value):
        display.append(3 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp;" + unicode(value))

    if getattr(dbo, 'dbo_id', None):
        append("key", dbo.dbo_key)
    elif dict_key:
        append("key", dict_key)

    if level == 0 or dbo.__class__ != getattr(dbo, 'dbo_base_class', None):
        append("class", cls_name(dbo.__class__))
    if getattr(dbo, 'dbo_set_key', None):
        append("set_key", dbo.dbo_set_key)
    for field in getattr(dbo, 'dbo_fields', []):
        append(field, getattr(dbo, field, "None"))

    for ref in getattr(dbo, 'dbo_refs', []):
        child_dbo = getattr(dbo, ref.field_name, None)
        if child_dbo:
            if follow_refs or not child_dbo.dbo_key_type:
                display.extend(dbo_describe(child_dbo, level + 1))
            else:
                append(ref.field_name, child_dbo.dbo_key)
        else:
            append(ref.field_name, "None")
    for col in getattr(dbo, 'dbo_lists', ()):
        child_coll = getattr(dbo, col.field_name)
        if child_coll:
            append(col.field_name, "")
            for child_dbo in child_coll:
                display.extend(dbo_describe(child_dbo, level + 1, False))
        else:
            append(col.field_name, "None")
    for col in getattr(dbo, 'dbo_maps', ()):
        child_coll = getattr(dbo, col.field_name)
        if child_coll:
            append(col.field_name, "")
            for child_dbo_id, child_dbo in child_coll.iteritems():
                display.extend(dbo_describe(child_dbo, level + 1, False, child_dbo_id))

    return display


def to_dbo_dict(dbo, use_defaults=False):
    dbo_dict = {}
    if dbo.__class__ != cls_registry(dbo.dbo_base_class):
        dbo_dict["class_name"] = cls_name(dbo.__class__)
    for field_name in dbo.dbo_fields:
        if use_defaults:
            default = getattr(dbo.__class__, field_name, None)
            instance = getattr(dbo, field_name, None)
            if instance != default:
                dbo_dict[field_name] = getattr(dbo, field_name, None)
        else:
            dbo_dict[field_name] = getattr(dbo, field_name, None)
    for coll_type in dbo.dbo_lists, dbo.dbo_maps:
        for dbo_col in coll_type:
            dbo_col.build_dict(dbo, dbo_dict, use_defaults)
    for dbo_ref in dbo.dbo_refs:
        try:
            dbo_dict[dbo_ref.field_name] = getattr(dbo, dbo_ref.field_name).dbo_id
        except AttributeError:
            pass
    return dbo_dict


class DBORef():
    def __init__(self, field_name, base_class, key_type=None):
        self.field_name = field_name
        self.base_class = base_class
        self.key_type = key_type


class DBOList(DBORef):
    coll_class = list

    def instance(self, dbo):
        instance = self.coll_class()
        setattr(dbo, self.field_name, instance)
        return instance

    def build_dict(self, dbo, dbo_dict, use_defaults):
        if use_defaults:
            try:
                dbo_list = dbo.__dict__[self.field_name]
            except KeyError:
                return
        else:
            dbo_list = getattr(dbo, self.field_name)
        self._add_raw_coll(dbo_dict, dbo_list, use_defaults)

    def _add_raw_coll(self, dbo_dict, dbo_list, use_defaults):
        if not use_defaults or dbo_list:
            dbo_dict[self.field_name] = [to_dbo_dict(child_dbo, use_defaults) for child_dbo in dbo_list]


class DBOMap(DBOList):
    coll_class = dict

    def _add_raw_coll(self, dbo_dict, dbo_list, use_defaults):
        if not use_defaults or dbo_list:
            dbo_dict[self.field_name] = {dbo_id: to_dbo_dict(child_dbo, use_defaults) for dbo_id, child_dbo in dbo_list.iteritems()}
