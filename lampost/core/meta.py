import logging

from lampost.datastore.classes import set_dbo_class, get_dbo_class
from lampost.datastore.dbofield import DBOTField, DBOField


log = logging.getLogger(__name__)


class CommonMeta(type):

    def __init__(cls, name, bases, new_attrs):
        cls._combine_base_fields(bases)
        if getattr(cls, 'template_id', None):
            cls._template_init()
        cls._update_actions(new_attrs)



    def _combine_base_fields(cls, bases):
        cls.class_providers = set()
        for base in bases:
            cls.class_providers.update(base.class_providers)


    def _update_actions(cls, new_attrs):
        cls.class_providers.update({func.__name__ for func in new_attrs.values() if hasattr(func, 'verbs')})


def call_mro(self, func_name, *args, **kwargs):
    for cls in reversed(self.__class__.__mro__):
        try:
            cls.__dict__[func_name](self, *args, **kwargs)
        except KeyError:
            pass



