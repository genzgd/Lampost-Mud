import logging
from lampost.datastore.auto import TemplateField
from lampost.datastore.classes import set_dbo_class, get_dbo_class, set_mixin, check_dbo_class

log = logging.getLogger(__name__)


class CommonMeta(type):
    dbo_fields = {}
    load_funcs = []
    class_providers = set()

    def __init__(cls, name, bases, new_attrs):
        cls._meta_init_attrs(new_attrs)
        cls._combine_base_fields(bases)
        cls._update_dbo_fields(new_attrs)
        if getattr(cls, 'template_id', None):
            cls._template_init()
        cls._update_actions(new_attrs)

        if 'class_id' in new_attrs:
            # Override any existing class id reference with this child class
            set_dbo_class(cls.class_id, cls)

        elif 'dbo_key_type' in new_attrs:
            # Override or set the class_id to the database key if present
            cls.class_id = cls.dbo_key_type
            set_dbo_class(cls.class_id, cls)

        if 'mixin_id' in new_attrs:
            set_mixin(cls.mixin_id, cls)

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

    def _combine_base_fields(cls, bases):
        cls.dbo_fields = {}
        cls.load_funcs = []
        cls.class_providers = set()
        for base in bases:
            cls.dbo_fields.update({name: dbo_field for name, dbo_field in base.dbo_fields.items()})
            cls.load_funcs.extend(base.load_funcs)
            cls.class_providers.update(base.class_providers)

    def _update_dbo_fields(cls, new_attrs):
        for name, attr in new_attrs.items():
            if hasattr(attr, 'hydrate_value'):
                old_attr = cls.dbo_fields.get(name)
                if old_attr != attr:
                    if old_attr:
                        log.info("Overriding attr {} of class {}", name, cls.__name__)
                    cls.dbo_fields[name] = attr
        load_func = new_attrs.get('on_loaded')
        if load_func:
            cls.load_funcs.append(load_func)

    def _template_init(cls):
        template_cls = get_dbo_class(cls.template_id)
        old_class = getattr(template_cls, 'instance_cls', None)
        if old_class:
            log.info("Overriding existing instance class {} with {} for template {}", old_class.__name__, cls.__name__,
                     cls.template_id)
        else:
            log.info("Initializing instance class {} for template {}", cls.__name__, cls.template_id)
        template_cls.add_dbo_fields(
            {name: dbo_field for name, dbo_field in cls.dbo_fields.items() if isinstance(dbo_field, TemplateField)})
        template_cls.instance_cls = cls
        cls.template_cls = template_cls


    def _update_actions(cls, new_attrs):
        cls.class_providers.update({func.__name__ for func in new_attrs.values() if hasattr(func, 'verbs')})


def call_mro(self, func_name, *args, **kwargs):
    for cls in reversed(self.__class__.__mro__):
        try:
            cls.__dict__[func_name](self, *args, **kwargs)
        except KeyError:
            pass


