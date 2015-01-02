from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField, TemplateField
from lampost.datastore.classes import get_dbo_class


m_requires(__name__, 'log', 'datastore')

# This is used as a 'thread local' type variable to collect child references while calculating save values
save_value_refs = []


class DBOField(AutoField):
    lazy = False

    def __init__(self, default=None, dbo_class_id=None, required=False):
        super().__init__(default)
        self.required = required
        self.dbo_class_id = dbo_class_id

    def save_value(self, instance):
        value = self.dto_value(instance)
        self.check_default(value, instance)
        return value

    def check_default(self, value, instance):
        if hasattr(self.default, 'save_value'):
            if value == self.default.save_value:
                raise KeyError
        elif value == self.default:
            raise KeyError

    def meta_init(self, field):
        self.field = field
        self.hydrate = get_hydrate_func(self.default, field, self.dbo_class_id)
        self.cmp_value = value_transform(to_dto_repr, self.default, field, self.dbo_class_id)
        self.dto_value = value_transform(to_dto_repr, self.default, field, self.dbo_class_id, for_json=True)



class DBOTField(DBOField, TemplateField):
    def check_default(self, value, instance):
        super().check_default(value, instance)
        try:
            template_value = getattr(instance.template, self.field)
        except AttributeError:
            return
        if hasattr(template_value, 'cmp_value'):
            if value == template_value.cmp_value:
                raise KeyError
        elif value == template_value:
            raise KeyError


def get_hydrate_func(default, field, class_id):
    def dbo_set(instance, dto_repr_list):
        value = {dbo for dbo in [load_ref(class_id, instance, dto_repr) for dto_repr in dto_repr_list] if
                 dbo is not None}
        setattr(instance, field, value)
        return value

    def dbo_list(instance, dto_repr_list):
        value = [dbo for dbo in [load_ref(class_id, instance, dto_repr) for dto_repr in dto_repr_list] if
                 dbo is not None]
        setattr(instance, field, value)
        return value

    def dbo_dict(instance, dto_repr_dict):
        value = {key: dbo for key, dbo in [(key, load_ref(class_id, instance, dto_repr))
                                           for key, dto_repr in dto_repr_dict.items()] if dbo is not None}
        setattr(instance, field, value)
        return value

    def dbo_simple(instance, dto_repr):
        value = load_ref(class_id, instance, dto_repr)
        setattr(instance, field, value)
        return value

    def native(instance, dto_repr):
        setattr(instance, field, dto_repr)
        return dto_repr

    if class_id:
        if isinstance(default, set):
            return dbo_set
        if isinstance(default, list):
            return dbo_list
        if isinstance(default, dict):
            return dbo_dict
        return dbo_simple
    return native


def value_transform(trans_func, default, field, class_id, for_json=False):
    def native(instance):
        return getattr(instance, field)

    def value_set(instance):
        return {trans_func(value, class_id) for value in getattr(instance, field) if value is not None}


    def value_list(instance):
        return [trans_func(value, class_id) for value in getattr(instance, field) if value is not None]

    def value_dict(instance):
        return {key: trans_func(value, class_id) for key, value in getattr(instance, field).items() if
                value is not None}

    def value_simple(instance):
        value = getattr(instance, field)
        return None if value is None else trans_func(value, class_id)

    if class_id:
        if isinstance(default, set) and not for_json:
            return value_set
        if isinstance(default, list) or isinstance(default, set):
            return value_list
        if isinstance(default, dict):
            return value_dict
        return value_simple

    return native


def to_dto_repr(dbo, class_id):
    if hasattr(dbo, 'dbo_id'):
        save_value_refs.append(dbo.dbo_key)
        return dbo.dbo_key if class_id == 'untyped' else dbo.dbo_id
    dto_value = dbo.dto_value
    if hasattr(dbo, 'template_key'):
        dto_value['tk'] = dbo.template_key
        save_value_refs.append(dbo.template_key)
    elif getattr(dbo, 'class_id', class_id) != class_id:
        # If the object has a different class_id than field definition thinks it should have
        # we need to save the actual class_id
        dto_value['class_id'] = dbo.class_id
    return dto_value


class DBOLField(DBOField):
    """
    This class should be used for database references where the value is used only for a short time, such
    as initializing the holder.  If used for collections it is important to remember that the underlying
    collection must hold dbo_ids, not actual objects.  The __set__ method does the conversion for
    """
    lazy = True

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            instance_value = instance.__dict__[self.field]
        except KeyError:
            return self._get_default(instance)
        return self._get_value(self.dbo_class_id, instance_value)

    def __set__(self, instance, value):
        if value == self.default:
            instance.__dict__.pop(self.field, None)
        else:
            instance.__dict__[self.field] = self._set_value(value)


def lazy_load(class_id, dbo_id):
    return load_object(dbo_id, class_id if class_id != "untyped" else None)


def load_ref(class_id, dbo_owner, dto_repr):
    if not dto_repr:
        return

    dbo_ref_id = None
    # The class_id passed in is what the field thinks it should hold
    # This can be overridden in the actual stored dictionary
    try:
        class_id = dto_repr['class_id']
    except TypeError:
        # A dto_repr is either a string or a dictionary.  If it's a string,
        # it must be reference, so capture the reference id
        dbo_ref_id = dto_repr
    except KeyError:
        pass

    dbo_class = get_dbo_class(class_id)
    if not dbo_class:
        return error('Unable to load reference for {}', class_id)

    # If this class has a key_type, it should always be a reference and we should load it from the database
    # The dto_representation in this case should always be a dbo_id
    if hasattr(dbo_class, 'dbo_key_type'):
        return load_object(dbo_ref_id, dbo_class)

    # If we still have a dbo_ref_id, this must be part of an untyped collection, so the dbo_ref_id is a
    # full value and we should be able to load it
    if dbo_ref_id:
        return load_object(dbo_ref_id)

    # If this is a template, it should have a template key, so we load the template from the database using
    # the full key, then hydrate any non-template fields from the dictionary
    template_key = dto_repr.get('tk')
    if template_key:
        template = load_object(template_key)
        if template:
            return template.create_instance(dbo_owner).hydrate(dto_repr)
        else:
            warn("Missing template for template_key {}", template_key)
            return

    # Finally, it's not a template and it is not a reference to an independent DB object, it must be a child
    # object of this class, just hydrate it and set the owner
    instance = dbo_class().hydrate(dto_repr)
    if instance:
        instance.dbo_owner = dbo_owner
        return instance