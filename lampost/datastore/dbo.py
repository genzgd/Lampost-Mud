import copy
from lampost.context.resource import m_requires

m_requires('log', 'datastore', 'encode', 'cls_registry', __name__)


class RootDBOMeta(type):
    def __init__(cls, class_name, bases, new_attrs):
        cls.dbo_fields = {}
        for base in bases:
            try:
                cls.dbo_fields.update({name: dbo_field for name, dbo_field in base.dbo_fields.iteritems() if name not in new_attrs.keys()})
            except AttributeError:
                pass
        cls._update_dbo_fields(new_attrs)

    def _update_dbo_fields(cls, new_attrs):
        for name, attr in new_attrs.iteritems():
            try:
                attr.meta_init(name)
            except AttributeError:
                pass
        cls.dbo_fields.update({name: dbo_field for name, dbo_field in new_attrs.iteritems() if hasattr(dbo_field, 'hydrate')})

    def add_dbo_fields(cls, new_fields):
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

    def __init__(self, dbo_id=None):
        if dbo_id:
            self.dbo_id = unicode(str(dbo_id).lower())

    def hydrate(self, dto):
        for field, dbo_field in self.dbo_fields.iteritems():
            if field in dto:
                dbo_field.hydrate(self, dto[field])
            else:
                try:
                    delattr(self, field)
                except AttributeError:
                    pass
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


class ProtoField(object):
    def __init__(self, default=None):
        self.default = default
        self.primitive = default is None or isinstance(default, (int, basestring, bool, tuple, float))
        if self.primitive:
            self._get_default = self._primitive_default
        else:
            self._get_default = self._complex_default

    def __get__(self, instance, owner=None):
        if not instance:
            return self
        try:
            return instance.__dict__[self.field]
        except KeyError:
            try:
                return getattr(instance.prototype, self.field)
            except AttributeError:
                return self._get_default(instance)

    def __set__(self, instance, value):
        if value == self.default:
            instance.__dict__.pop(self.field, None)
        else:
            instance.__dict__[self.field] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self.field, None)

    def _primitive_default(self, instance):
        return self.default

    def _complex_default(self, instance):
        new_value = copy.copy(self.default)
        instance.__dict__[self.field] = new_value
        return new_value

    def meta_init(self, field):
        self.field = field


class DBOField(ProtoField):
    def __init__(self, default=None, dbo_class_id=None):
        super(DBOField, self).__init__(default)
        self.dbo_class_id = dbo_class_id
        if self.dbo_class_id:
            if self.primitive:
                self.hydrate_dto = self.dbo_from_repr
            elif hasattr(self.default, '__iter__'):
                self.hydrate_dto = self.dbo_list_from_repr
            elif hasattr(self.default, '__getitem__'):
                self.hydrate_dto = self.dbo_dict_from_repr
        else:
            self.hydrate_dto = lambda dto_repr, instance: dto_repr

    def hydrate(self, instance, dto_repr):
        self.dbo_class = cls_registry(self.dbo_class_id)
        setattr(instance, self.field, self.hydrate_dto(dto_repr, instance))

    def dbo_from_repr(self, dto_repr, instance):
        return self.dbo_class.load_ref(dto_repr, instance)

    def dbo_list_from_repr(self, dto_repr, instance):
        return [self.dbo_from_repr(single_repr, instance) for single_repr in dto_repr]

    def dbo_dict_from_repr(self, dto_repr, instance):
        return {dbo.dbo_id: dbo for dbo in dbo_list_from_repr(dto_repr, instance)}

    def to_dto(self, instance, dto):
        dto[self.field] = self.dto_value(instance)

    def to_save_dto(self, instance, save_dto):
        try:
            save_dto[self.field] = self.save_dto_value(instance)
        except KeyError:
            pass
