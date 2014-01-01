import copy
from lampost.context.resource import m_requires
from lampost.util.lmutil import cls_name

m_requires('log', 'datastore', 'encode', 'cls_registry', __name__)


class RootDBOMeta(type):

    def __init__(cls, class_name, bases, new_attrs):

        def build_coll(coll_name):
            coll = set()
            for base in bases:
                coll.update(base.__dict__.get(coll_name, ()))
            coll.update(new_attrs.get(coll_name, ()))
            setattr(cls, coll_name, coll)

        build_coll('dbo_fields')
        build_coll('dbo_maps')

        for name, attr in new_attrs.iteritems():
            try:
                attr.dbo_init(cls, name)
                cls.dbo_fields.add(name)
            except AttributeError:
                pass


class RootDBO(object):
    __metaclass__ = RootDBOMeta
    dbo_key_type = None
    dbo_set_key = None

    dbo_indexes = ()

    @classmethod
    def load_ref(cls, dbo_id):
        return load_object(cls, dbo_id)

    def __init__(self, dbo_id=None):
        if dbo_id:
            self.dbo_id = unicode(str(dbo_id).lower())

    def hydrate(self, dto):
        for field in self.dbo_fields:
            try:
                dto_value = dto[field]
                try:
                    dbo_field = getattr(self.__class__, field)
                    dbo_field.hydrate_set(self, dto_value)
                except AttributeError as exp:
                    setattr(self, field, dto_value)
            except KeyError:
                self.__dict__.pop(field, None)
        return self

    def on_created(self):
        pass

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
        dbo_dict['dbo_key_type'] = getattr(self, 'class_id', self.dbo_key_type)
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

    if getattr(dbo, 'dbo_key', None):
        append("key", dbo.dbo_key)
    elif dict_key:
        append("key", dict_key)

    if getattr(dbo, 'dbo_set_key', None):
        append("set_key", dbo.dbo_set_key)
    for field in getattr(dbo, 'dbo_fields', []):
        append(field, getattr(dbo, field, "None"))

    for col in getattr(dbo, 'dbo_maps', ()):
        child_coll = getattr(dbo, col.field_name)
        if child_coll:
            append(col.field_name, "")
            for child_dbo_id, child_dbo in child_coll.iteritems():
                display.extend(dbo_describe(child_dbo, level + 1, False, child_dbo_id))

    return display


def to_dbo_dict(dbo, exclude_defaults=False):
    dbo_dict = {}
    for field_name in dbo.dbo_fields:
        if exclude_defaults:
            default = getattr(dbo.__class__, field_name, None)
            instance = getattr(dbo, field_name, None)
            if instance != default:
                dbo_dict[field_name] = getattr(dbo, field_name, None)
        else:
            dbo_dict[field_name] = getattr(dbo, field_name, None)

    for dbo_col in dbo.dbo_maps:
        dbo_col.build_dict(dbo, dbo_dict, exclude_defaults)

    return dbo_dict


def primitive_getter(self, instance):
    return instance.__dict__.get(self.field, self.default)


def complex_getter(self, instance):
    try:
        return instance.__dict__[self.field]
    except KeyError:
        new_value = copy.copy(self.default)
        instance.__dict__[self.field] = new_value
        return new_value


def list_setter(self, instance, dto_list):
    instance.__dict__[self.field] = [cls_registry(self.dbo_class)().hydrate(dto) for dto in dto_list]


class DBOField(object):

    def __init__(self, default=None, dbo_class=None):
        self.default = default
        self.dbo_class = dbo_class
        if self.dbo_class and hasattr(default, 'append'):
            self.hydrate_set = list_setter.__get__(self)
        if default is None or isinstance(default, (int, basestring, bool, tuple, float)):
            self.getter = primitive_getter.__get__(self)
        else:
            self.getter = complex_getter.__get__(self)

    def __get__(self, instance, owner=None):
        if not instance:
            return self
        return self.getter(instance)

    def __set__(self, instance, value):
        if value == self.default:
            instance.__dict__.pop(self.field, None)
        else:
            instance.__dict__[self.field] = value

    def hydrate_set(self, instance, dto_value):
        return self.__set__(instance, dto_value)

    def dbo_init(self, owner, field):
        self.owner = owner
        self.field = field

    def hydrate_dto(self, instance, dto):
        dto[self.field] = self.__get__(instance)

    def hydrate_save_dto(self, instance, save_dto):
        try:
            save_dto[self.field] = instance.__dict__[self.field]
        except KeyError:
            pass


class DBORef(object):

    def __init__(self, dbo_class, lazy=False):
        self.dbo_class = dbo_class
        self.lazy = lazy

    def __get__(self, instance, owner=None):
        if self.lazy:
            try:
                return dbo_class.load_ref(instance.__dict__[self.ref_id])
            except KeyError:
                pass
        else:
            return instance.__dict__[self.field]

    def __set__(self, instance, dbo_id):
        if dbo_id:
            if self.lazy:
                instance.__dict__[self.ref_id] = dbo_id
            else:
                instance.__dict__[self.field] = self.dbo_class.load_ref(dbo_id)
        else:
            instance.__dict__.pop(self.field, None)

    def dbo_init(self, owner, field):
        self.owner = owner
        self.field = field
        if self.lazy:
            self.ref_id = '_{}_ref'.format(field)

    def hydrate_dto(self, instance, dto_dict):
        dto_dict[self.field] = instance.__dict__.get(self.ref_id, None)

    def hydrate_dbo(self, instance, dto_dict):
        try:
            dto_dict[self.field] = instance.__dict__[self.ref_id]
        except KeyError:
            pass


class DBOMap(object):
    coll_class = dict

    def __init__(self, field_name, base_class):
        self.field_name = field_name
        self.base_class = base_class

    def instance(self, dbo):
        instance = self.coll_class()
        setattr(dbo, self.field_name, instance)
        return instance

    def build_dict(self, dbo, dbo_dict, exclude_defaults):
        if exclude_defaults:
            try:
                dbo_list = dbo.__dict__[self.field_name]
            except KeyError:
                return
        else:
            dbo_list = getattr(dbo, self.field_name)
        self._add_raw_coll(dbo_dict, dbo_list, exclude_defaults)

    def _add_raw_coll(self, dbo_dict, dbo_map, exclude_defaults):
        if dbo_map or not exclude_defaults:
            dbo_dict[self.field_name] = {dbo_id: to_dbo_dict(child_dbo, exclude_defaults) for dbo_id, child_dbo in dbo_map.iteritems()}
