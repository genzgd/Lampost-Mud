from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField, TemplateField
from lampost.datastore.classes import get_dbo_class


m_requires(__name__, 'log', 'datastore')

# This is used as a 'thread local' type variable to collect child references while calculating save values
save_value_refs = []


class DBOField(AutoField):
    def __init__(self, default=None, dbo_class_id=None, required=False):
        super().__init__(default)
        self.required = required
        self.dbo_class_id = dbo_class_id

    def save_value(self, instance):
        value = self._save_value(instance)
        self.check_default(value, instance)
        return value

    def hydrate(self, instance, dto_repr):
        value = self._hydrate_func(instance, dto_repr)
        setattr(instance, self.field, value)
        return value

    def check_default(self, value, instance):
        if hasattr(self.default, 'save_value'):
            if value == self.default.save_value:
                raise KeyError
        elif value == self.default:
            raise KeyError

    def meta_init(self, field):
        self.field = field
        self._hydrate_func = get_hydrate_func(load_any, self.default, self.dbo_class_id)
        self.dto_value = value_transform(to_dto_repr, self.default, field, self.dbo_class_id, for_json=True)
        self.cmp_value = value_transform(to_save_repr, self.default, field, self.dbo_class_id)
        self._save_value = value_transform(to_save_repr, self.default, field, self.dbo_class_id, for_json=True)


class DBOTField():
    """
    This class always passes access to the template.  It also provides a blueprint to auto generate the appropriate
    DBO fields in the Template class.

    Fields that are initialized in the Template but whose values can be overridden by the instance should be declared
    as a DBOField in the template class and a DBOCField field in the instance class with identical names
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance.template, self.field)

    def __set__(self, instance, value):
        error("Illegally setting value {} of DBOTField {}", value, self.field,  stack_info=True)

    def meta_init(self, field):
        self.field = field


class DBOCField(DBOField, TemplateField):
    """
    This class should be used in cloneable objects that do not have a separate template class.  It will pass
    access to the original object if not overridden in the child object.
    """
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


class DBOLField(DBOField):
    """
    This class should be used for database references where the value is used only for a short time, such
    as initializing the holder.  It 'lazy loads' the database object when the descriptor __get__ is called,
    so no database access is made if the field is never 'read', and the database object will be freed from the
    db cache on garbage collection if any reads have since gone out of scope

    Sets are not supported to simplify transforms to JSON
    """
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            value = instance.__dict__[self.field]
        except KeyError:
            value = self._get_default(instance)
        return self._hydrate_func(instance, value)

    def __set__(self, instance, value):
        if value == self.default:
            instance.__dict__.pop(self.field, None)
        else:
            instance.__dict__[self.field] = self._set_value(value)

    def hydrate(self, instance, dto_repr):
        instance.__dict__[self.field] = dto_repr
        return dto_repr

    def cmp_value(self, instance):
        return instance.__dict__.get(self.field, self.default)

    def dto_value(self, instance):
        return instance.__dict__.get(self.field, self.default)

    def _save_value(self, instance):
        return instance.__dict__.get(self.field, self.default)

    def meta_init(self, field):
        self.field = field
        self._hydrate_func = get_hydrate_func(load_keyed, self.default, self.dbo_class_id)
        self._set_value = value_transform(to_dbo_key, self.default, field, self.dbo_class_id)


def get_hydrate_func(load_func, default, class_id):
    def dbo_set(instance, dto_repr_list):
        return {dbo for dbo in [load_func(class_id, instance, dto_repr) for dto_repr in dto_repr_list] if
                 dbo is not None}

    def dbo_list(instance, dto_repr_list):
        return [dbo for dbo in [load_func(class_id, instance, dto_repr) for dto_repr in dto_repr_list] if
                 dbo is not None]

    def dbo_dict(instance, dto_repr_dict):
        return {key: dbo for key, dbo in [(key, load_func(class_id, instance, dto_repr))
                                           for key, dto_repr in dto_repr_dict.items()] if dbo is not None}

    def dbo_simple(instance, dto_repr):
        return load_func(class_id, instance, dto_repr)

    def native(instance, dto_repr):
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
        return dbo.dbo_key if class_id == 'untyped' else dbo.dbo_id
    dto_value = dbo.dto_value
    if hasattr(dbo, 'template_key'):
        dto_value['tk'] = dbo.template_key
    elif getattr(dbo, 'class_id', class_id) != class_id:
        # If the object has a different class_id than field definition thinks it should have
        # we need to save the actual class_id
        dto_value['class_id'] = dbo.class_id
    return dto_value


def to_save_repr(dbo, class_id):
    if hasattr(dbo, 'dbo_id'):
        save_value_refs.append(dbo.dbo_key)
        return dbo.dbo_key if class_id == 'untyped' else dbo.dbo_id
    save_value = dbo.save_value
    if hasattr(dbo, 'template_key'):
        save_value['tk'] = dbo.template_key
        save_value_refs.append(dbo.template_key)
    elif getattr(dbo, 'class_id', class_id) != class_id:
        # If the object has a different class_id than field definition thinks it should have
        # we need to save the actual class_id
        save_value['class_id'] = dbo.class_id
    return save_value


def to_dbo_key(dbo, class_id):
    try:
        return dbo.dbo_key if class_id == 'untyped' else dbo.dbo_id
    except AttributeError:
        error('Attempting to set dbo_ref with unkeyed value {}', dbo)


def load_keyed(class_id, dbo_owner, dbo_id):
    return load_object(dbo_id, class_id if class_id != "untyped" else None)


def load_any(class_id, dbo_owner, dto_repr):
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
