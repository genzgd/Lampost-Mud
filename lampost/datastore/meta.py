import itertools
from lampost.datastore.auto import TemplateField
from lampost.datastore.classes import set_dbo_class, add_sub_class, get_dbo_class


class CommonMeta(type):

    dbo_fields = {}
    load_funcs = []
    class_providers = set()

    def __init__(cls, name, bases, new_attrs):
        cls._meta_init_attrs(new_attrs)
        cls._combine_dbo_fields(bases)
        cls._update_dbo_fields(new_attrs)
        cls._template_init()
        cls._update_actions(new_attrs)
        if 'class_id' in new_attrs:
            set_dbo_class(cls.class_id, cls)
        elif 'sub_class_id' in new_attrs:
            set_dbo_class(cls.sub_class_id, cls)
            add_sub_class(cls)
        elif hasattr(cls, 'dbo_key_type'):
            set_dbo_class(cls.dbo_key_type, cls)

    def add_dbo_fields(cls, new_fields):
        cls._meta_init_attrs(new_fields)
        cls._update_dbo_fields(new_fields)
        for name, dbo_field in new_fields.items():
            setattr(cls, name, dbo_field)

    def _meta_init_attrs(cls, new_attrs):
        for name, attr in new_attrs.items():
            try:
                attr.meta_init(name)
            except AttributeError:
                pass

    def _combine_dbo_fields(cls, bases):
        cls.dbo_fields = {}
        cls.load_funcs = []
        for base in bases:
            cls.dbo_fields.update({name: dbo_field for name, dbo_field in base.dbo_fields.items()})
            cls.load_funcs.extend(base.load_funcs)

    def _update_dbo_fields(cls, new_attrs):
        cls.dbo_fields.update({name: attr for name, attr in new_attrs.items() if hasattr(attr, 'hydrate_value')})

        load_func = new_attrs.get('on_loaded')
        if load_func:
            cls.load_funcs = cls.load_funcs.copy()
            cls.load_funcs.append(load_func)

    def _template_init(cls):
        if not hasattr(cls, 'template_id'):
            return
        cls.class_id = '{}_inst'.format(cls.template_id)
        set_dbo_class(cls.class_id, cls)
        template_cls = get_dbo_class(cls.template_id)
        template_cls.add_dbo_fields({name: dbo_field for name, dbo_field in cls.dbo_fields.items() if isinstance(dbo_field, TemplateField)})
        template_cls.instance_cls = cls

    def _update_actions(cls, new_attrs):
        cls.class_providers = cls.class_providers.copy()
        cls.class_providers.update({func.__name__ for func in new_attrs.values() if hasattr(func, 'verbs')})