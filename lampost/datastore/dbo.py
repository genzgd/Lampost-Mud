from lampost.datastore.classes import get_dbo_class, set_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.auto import TemplateField, AutoField
from lampost.datastore.meta import CommonMeta

m_requires(__name__, 'log', 'datastore')


class RootDBO(metaclass=CommonMeta):
    dbo_key_type = None
    dbo_key_sort = None
    dbo_parent_type = None
    dbo_owner = None
    dbo_children_types = []
    dbo_indexes = ()
    template_id = None

    @classmethod
    def dbo_defs(cls, key):
        return ':'.join([cls.dbo_key_type, key]), key, cls.dbo_key_type

    def __init__(self, dbo_id=None):
        if dbo_id:
            self.dbo_id = str(dbo_id).lower()

    def _on_loaded(self):
        for load_func in reversed(self.load_funcs):
            load_func(self)

    def hydrate(self, dto):
        for field, dbo_field in self.dbo_fields.items():
            if field in dto:
                dbo_value = dbo_field.hydrate_value(dto[field], self)
                setattr(self, field, dbo_value)
            else:
                dbo_value = None
                try:
                    delattr(self, field)
                except AttributeError:
                    pass
            if not dbo_value and dbo_field.required:
                warn("Missing required field {} in object {}", field, dto)
                return None
        self._on_loaded()
        return self

    def clone(self):
        clone = self.__class__(getattr(self, 'dbo_id', None))
        clone.template = self
        clone._on_loaded()
        return clone

    @property
    def save_value(self):
        save_value = {}
        for field, dbo_field in self.dbo_fields.items():
            try:
                save_value[field] = dbo_field.save_value(self)
            except KeyError:
                continue
        return self.metafields(save_value, ['template_key'])

    def on_created(self):
        pass

    def on_deleted(self):
        pass

    def describe(self):
        return self._describe([], 0)

    @property
    def dbo_key(self):
        return ":".join([self.dbo_key_type, self.dbo_id])

    @property
    def parent_id(self):
        if self.dbo_id:
            return self.dbo_id.split(':')[0]

    @property
    def dbo_set_key(self):
        if self.dbo_parent_type:
            return "{}_{}s:{}".format(self.dbo_parent_type, self.dbo_key_type, self.parent_id)


    @property
    def dto_value(self):
        dto_value = {field: dbo_field.dto_value(getattr(self, field)) for field, dbo_field in self.dbo_fields.items()}
        for child_type in self.dbo_children_types:
            dto_value['{}_list'.format(child_type)] = self.dbo_child_keys(child_type)
        return self.metafields(dto_value, ['dbo_id', 'class_id', 'template_key', 'dbo_key_type', 'dbo_parent_type',
                                           'dbo_children_types'])

    def dbo_child_keys(self, child_type):
        if getattr(self, 'dbo_id', None):
            child_class = get_dbo_class(child_type)
            return sorted(fetch_set_keys("{}_{}s:{}".format(self.dbo_key_type, child_type, self.dbo_id)),
                          key=child_class.dbo_key_sort)
        return []

    def autosave(self):
        save_object(self, autosave=True)

    def metafields(self, dto_repr, field_names):
        for metafield in field_names:
            try:
                dto_repr[metafield] = getattr(self, metafield)
            except AttributeError:
                pass
        return dto_repr

    def _describe(self, display, level):

        def append(value, key):
            display.append(4 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp;" + str(value))

        if getattr(self, 'class_id', None):
            append(self.class_id, 'class_id')
        if getattr(self,'dbo_key_type', None):
            append(self.dbo_key_type, 'dbo_key_type')
        if getattr(self, 'dbo_id', None):
            append(self.dbo_id, 'dbo_id')
            level *= 99
        if getattr(self, 'template_key', None):
            append(self.template_key, 'template_key')
            level *= 99
        if level > 3:
            return
        for field, dbo_field in sorted(self.dbo_fields.items(), key=lambda field_value: field_value[0]):
            value = getattr(self, field)
            if value:
                wrapper = value_wrapper(value)
                if hasattr(dbo_field, 'dbo_class_id'):
                    append('', field)
                    wrapper(lambda value : value._describe(display, level + 1))(value)
                else:
                    wrapper(append)(value, field)
        return display


class Untyped():
    dbo_key_type = None

    @classmethod
    def dbo_defs(cls, key):
        try:
            key_parts = key.split(':')
        except Exception:
            return
        return key, ':'.join(key_parts[1:]), key_parts[0]

    def hydrate(self, dto_repr):
        warn("Attempting to hydrate invalid dto {}", dto_repr)


set_dbo_class('untyped', Untyped)


def load_ref(class_id, dbo_repr, dbo_owner=None):
    if not dbo_repr:
        return

    cls = get_dbo_class(class_id)
    if not cls:
        return error('Unable to load reference for {}', class_id)

    if cls.dbo_key_type:
        return load_object(cls, dbo_repr)

    try:
        return load_object(cls, dbo_repr['dbo_key'])
    except KeyError:
        pass

    template_key = dbo_repr.get('template_key')
    if template_key:
        template = load_object(Untyped, template_key)
        if template:
            instance = template.create_instance(dbo_owner).hydrate(dbo_repr)
            if instance:
                instance.on_created()
            return instance
        else:
            warn("Missing template for template_key {}", template_key)
            return
    instance = cls().hydrate(dbo_repr)
    if instance:
        instance.dbo_owner = dbo_owner
    return instance


def to_dto_repr(value):
    try:
        return value.dbo_id
    except AttributeError:
        try:
            return value.dto_value
        except AttributeError:
            return None


class DBOField(AutoField):
    def __init__(self, default=None, dbo_class_id=None, required=False):
        super().__init__(default)
        self.required = required
        if dbo_class_id:
            self.dbo_class_id = dbo_class_id
            self.value_wrapper = value_wrapper(self.default)
            self.hydrate_value = value_wrapper(self.default, False)(self.hydrate_dbo_value)
            self.convert_save_value = value_wrapper(self.default)(save_repr)
            self.dto_value = value_wrapper(self.default)(to_dto_repr)
        else:
            self.hydrate_value = lambda dto_repr, instance: dto_repr
            self.convert_save_value = lambda value: value
            self.dto_value = lambda value: value

    def hydrate_dbo_value(self, dto_repr, instance):
        return load_ref(self.dbo_class_id, dto_repr, instance)

    def save_value(self, instance):
        value = self.convert_save_value(instance.__dict__[self.field])
        self.should_save(value, instance)
        return value

    def should_save(self, value, instance):
        self.check_default(value)

    def check_default(self, value):
        if hasattr(self.default, 'save_value'):
            if value == self.default.save_value:
                raise KeyError
        elif value == self.default:
            raise KeyError


class DBOTField(DBOField, TemplateField):
    def should_save(self, value, instance):
        self.check_default(value)
        try:
            template_value = getattr(instance.template, self.field)
        except AttributeError:
            return
        if hasattr(template_value, 'save_value'):
            if value == template_value:
                raise KeyError
        elif value == template_value:
            raise KeyError


def save_repr(value):
    if hasattr(value, 'dbo_id'):
        return {'dbo_key': value.dbo_key}
    return value.save_value



def value_wrapper(value, for_dto=True):
    if isinstance(value, set):
        return list_wrapper if for_dto else set_wrapper
    if isinstance(value, dict):
        return dict_wrapper
    if isinstance(value, list):
        return list_wrapper
    return lambda x: x


def set_wrapper(func):
    def wrapper(*args):
        return {value for value in [func(single, *args[1:]) for single in args[0]]
                if value is not None}

    return wrapper


def list_wrapper(func):
    def wrapper(*args):
        return [value for value in [func(single, *args[1:]) for single in args[0]]
                if value is not None]

    return wrapper


def dict_wrapper(func):
    def wrapper(*args):
        return {key: value for key, value in [(key, func(single, *args[1:])) for key, single in args[0].items()]
                if value is not None}

    return wrapper
