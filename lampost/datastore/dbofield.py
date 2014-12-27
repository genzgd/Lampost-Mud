from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField, TemplateField
from lampost.datastore.classes import get_dbo_class


m_requires(__name__, 'log', 'datastore')


class DBOField(AutoField):
    def __init__(self, default=None, dbo_class_id=None, required=False):
        super().__init__(default)
        self.required = required
        if dbo_class_id:
            self.dbo_class_id = dbo_class_id
            self.value_wrapper = value_wrapper(self.default)
            self.hydrate_value = value_wrapper(self.default, False)(self.hydrate_dbo_value)
            self.convert_save_value = value_wrapper(self.default)(save_repr)
            self.dto_value = value_wrapper(self.default)(self.to_dto_repr)
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

    def to_dto_repr(self, value):
        try:
            return value.dbo_key if self.dbo_class_id == 'untyped' else value.dbo_id
        except AttributeError:
            try:
                dto = value.dto_value
                field_class = getattr(self, 'dbo_class_id', None)
                if getattr(value, 'class_id', field_class) != field_class:
                    dto['class_id'] = value.class_id
                if hasattr(value, 'template_key'):
                    dto['template_key'] = value.template_key
                return dto
            except AttributeError:
                return None

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


def load_ref(class_id, dbo_repr, dbo_owner=None):
    if not dbo_repr:
        return

    dbo_ref_id = None
    # The class_id passed in is what the field thinks it should hold
    # This can be overridden in the actual stored dictionary
    try:
        class_id = dbo_repr['class_id']
    except TypeError:
        # A dbo_repr is either a string or a dictionary.  If it's a string,
        # it must be reference, so capture the reference id
        dbo_ref_id = dbo_repr
    except KeyError:
        pass

    dbo_class = get_dbo_class(class_id)
    if not dbo_class:
        return error('Unable to load reference for {}', class_id)

    # If this class has a key_type, it should always be a reference and we should load it from the database
    # The dbo_representation in this case should always be a dbo_id
    if hasattr(dbo_class, 'dbo_key_type'):
        return load_object(dbo_ref_id, dbo_class)

    # If we still have a dbo_ref_id, this must be part of an untyped collection, so the dbo_ref_id is a
    # full value and we should be able to load it
    if dbo_ref_id:
        return load_object(dbo_ref_id)

    # If this is a template, it should have a template key, so we load the template from the database using
    # the full key, then hydrate any non-template fields from the dictionary
    template_key = dbo_repr.get('tk')
    if template_key:
        template = load_object(template_key)
        if template:
            return template.create_instance(dbo_owner).hydrate(dbo_repr)
        else:
            warn("Missing template for template_key {}", template_key)
            return

    # Finally, it's not a template and it is not a reference to an independent DB object, it must be a child
    # object of this class, just hydrate it and set the owner
    instance = dbo_class().hydrate(dbo_repr)
    if instance:
        instance.dbo_owner = dbo_owner
        return instance


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