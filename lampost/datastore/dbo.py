import copy

from collections import defaultdict
from lampost.context.resource import m_requires
from lampost.datastore.proto import ProtoMeta

m_requires('log', 'datastore', 'encode', 'cls_registry', __name__)

dbo_field_classes = defaultdict(set)

_init_priority = 10000


def _post_init():
    for class_id, dbo_fields in dbo_field_classes.iteritems():
        dbo_class = cls_registry(class_id)
        for dbo_field in dbo_fields:
            dbo_field.dbo_class = dbo_class
    dbo_field_classes.clear()


class RootDBOMeta(ProtoMeta):
    def __init__(cls, class_name, bases, new_attrs):
        super(RootDBOMeta, cls).__init__(class_name, bases, new_attrs)
        cls.dbo_fields = {}
        for base in bases:
            try:
                cls.dbo_fields.update({name: dbo_field for name, dbo_field in base.dbo_fields.iteritems() if name not in new_attrs.keys()})
            except AttributeError:
                pass
        cls._update_dbo_fields(new_attrs)

    def _update_dbo_fields(cls, new_attrs):
        cls.dbo_fields.update({name: dbo_field for name, dbo_field in new_attrs.iteritems() if hasattr(dbo_field, 'hydrate_value')})

    def add_dbo_fields(cls, new_fields):
        cls._meta_init_attrs(new_fields)
        cls._update_dbo_fields(new_fields)
        for name, dbo_field in new_fields.iteritems():
            setattr(cls, name, dbo_field)


class RootDBO(object):
    __metaclass__ = RootDBOMeta
    dbo_key_type = None
    dbo_set_key = None

    dbo_indexes = ()

    @classmethod
    def load_ref(cls, dbo_repr, owner=None):
        if cls.dbo_key_type:
            return load_object(cls, dbo_repr)
        return cls().hydrate(dbo_repr)

    @classmethod
    def to_dto_repr(cls, value):
        try:
            return value.dbo_id
        except AttributeError:
            return value.dto_value

    @classmethod
    def to_save_repr(cls, value):
        try:
            return value.dbo_id
        except AttributeError:
            return value.save_value

    def __init__(self, dbo_id=None):
        if dbo_id:
            self.dbo_id = unicode(str(dbo_id).lower())

    def hydrate(self, dto):
        for field, dbo_field in self.dbo_fields.iteritems():
            if field in dto:
                setattr(self, field, dbo_field.hydrate_value(dto[field], self))
            else:
                try:
                    delattr(self, field)
                except AttributeError:
                    pass
        return self

    @property
    def save_value(self):
        save_value = {}
        for field, dbo_field in self.dbo_fields.iteritems():
            try:
                save_value[field] = dbo_field.save_value(self)
            except KeyError:
                continue
        return self.metafields(save_value, ['dbo_id', 'class_id'])

    def to_dto_dict(self):
        return

    def on_created(self):
        pass

    def on_loaded(self):
        pass

    @property
    def dbo_key(self):
        return unicode(":".join([self.dbo_key_type, self.dbo_id]))

    @property
    def dto_value(self):
        dto_value = {field: dbo_field.dto_value(getattr(self, field)) for field, dbo_field in self.dbo_fields.iteritems()}
        dto_value['dbo_key_type'] = getattr(self, 'class_id', self.dbo_key_type)
        return self.metafields(dto_value, ['dbo_id', 'class_id', 'template_id'])

    def autosave(self):
        save_object(self, autosave=True)

    def rec_describe(self):
        return dbo_describe(self)

    def metafields(self, dto_repr, field_names):
        for metafield in field_names:
            try:
                dto_repr[metafield] = getattr(self, metafield)
            except AttributeError:
                pass
        return dto_repr


def dbo_describe(dbo, level=0):
    display = []

    def append(key, value):
        display.append(3 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp;" + unicode(value))

    if getattr(dbo, 'dbo_key', None):
        append("key", dbo.dbo_key)
    if getattr(dbo, 'dbo_set_key', None):
        append("set_key", dbo.dbo_set_key)
    for field in getattr(dbo, 'dbo_fields', []):
        child = getattr(dbo, field)
        append(field, child)
        if level == 0:
            display.extend(dbo_describe(child, 1))
    return display


class ProtoField(object):
    def __init__(self, default=None):
        self.default = default
        if default is None or isinstance(default, (int, basestring, bool, tuple, float)):
            self._get_default = lambda instance: self.default
        else:
            self._get_default = self._complex_default

    def __get__(self, instance, owner=None):
        if not instance:
            return self
        try:
            return instance.__dict__[self.field]
        except KeyError:
            try:
                return getattr(instance.template, self.field)
            except AttributeError:
                return self._get_default(instance)

    def __set__(self, instance, value):
        if value == self.default:
            instance.__dict__.pop(self.field, None)
        else:
            instance.__dict__[self.field] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self.field, None)

    def _complex_default(self, instance):
        new_value = copy.copy(self.default)
        instance.__dict__[self.field] = new_value
        return new_value

    def meta_init(self, field):
        self.field = field


class DBOField(ProtoField):
    dbo_field = True

    def __init__(self, default=None, dbo_class_id=None):
        super(DBOField, self).__init__(default)
        if dbo_class_id:
            dbo_field_classes[dbo_class_id].add(self)
            if isinstance(self.default, dict):
                wrapper = dict_wrapper
            elif isinstance(self.default, list):
                wrapper = list_wrapper
            else:
                wrapper = lambda x: x
            self.hydrate_value = wrapper(self.hydrate_dbo_value)
            self.convert_save_value = wrapper(self.dbo_save_value)
            self.dto_value = wrapper(self.dbo_dto_value)
        else:
            self.hydrate_value = lambda dto_repr, instance: dto_repr
            self.convert_save_value = lambda value: value
            self.dto_value = lambda value: value

    def dbo_dto_value(self, dbo_value):
        return self.dbo_class.to_dto_repr(dbo_value)

    def dbo_save_value(self, dbo_value):
        return self.dbo_class.to_save_repr(dbo_value)

    def hydrate_dbo_value(self, dto_repr, instance):
        return self.dbo_class.load_ref(dto_repr, instance)

    def save_value(self, instance):
        value = self.convert_save_value(instance.__dict__[self.field])
        if value == self.default:
            raise KeyError
        try:
            if value == getattr(instance.template, self.field):
                raise KeyError
        except AttributeError:
            pass
        return value


def list_wrapper(func):
    def wrapper(*args):
        return [value for value in [func(single, *args[1:]) for single in args[0]]
                if value is not None]

    return wrapper


def dict_wrapper(func):
    def wrapper(*args):
        return {key: value for key, value in [(key, func(single, *args[1:])) for key, single in args[0].viewitems()]
                if value is not None}

    return wrapper
