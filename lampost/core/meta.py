import logging

from lampost.datastore.classes import set_dbo_class, get_dbo_class
from lampost.datastore.dbofield import DBOTField, DBOField


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
        cls.dbot_fields = {}
        cls.dbo_fields = {}
        cls.load_funcs = []
        cls.class_providers = set()
        for base in bases:
            cls.dbo_fields.update({name: dbo_field for name, dbo_field in base.dbo_fields.items()})
            cls.load_funcs.extend(base.load_funcs)
            cls.class_providers.update(base.class_providers)
            cls.dbot_fields.update({name: dbot_field for name, dbot_field in base.dbot_fields.items()})

    def _update_dbo_fields(cls, new_attrs):
        for name, attr in new_attrs.items():
            if hasattr(attr, 'hydrate'):
                old_attr = cls.dbo_fields.get(name)
                if old_attr != attr:
                    if old_attr and old_attr.default == attr.default:
                        log.warn("Unnecessary override of attr {} in class {}", name, cls.__name__)
                    elif old_attr and old_attr.default:
                        log.info("Overriding default value of attr{} in class {}", name, cls.__name__)
                    cls.dbo_fields[name] = attr
            elif isinstance(attr, DBOTField):
                cls.dbot_fields[name] = attr
        load_func = new_attrs.get('on_loaded')
        if load_func:
            cls.load_funcs.append(load_func)

    def _template_init(cls):
        template_cls = get_dbo_class(cls.template_id)
        old_class = getattr(template_cls, 'instance_cls', None)
        if old_class:
            existing_fields = old_class.dbot_fields.values()
            log.info("Overriding existing instance class {} with {} for template {}", old_class.__name__, cls.__name__,
                     cls.template_id)
        else:
            log.info("Initializing instance class {} for template {}", cls.__name__, cls.template_id)
            existing_fields = ()
        new_dbo_fields = {name: DBOField(*dbo_field.args, **dbo_field.kwargs) for name, dbo_field in
                          cls.dbot_fields.items() if dbo_field not in existing_fields}
        template_cls.add_dbo_fields(new_dbo_fields)
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



