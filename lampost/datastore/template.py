from lampost.context.resource import m_requires
from lampost.core.test import CoreMeta
from lampost.datastore.classes import get_dbo_class
from lampost.datastore.dbofield import DBOTField

m_requires(__name__, 'log')


class Template(metaclass=CoreMeta):

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.template = self
        instance.template_key = self.dbo_key
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass


class InstanceDBO(metaclass=CoreMeta):
    dbot_fields = {}

    @classmethod
    def _mixin_init(cls, name, bases, new_attrs):
        cls.dbot_fields = cls.dbot_fields.copy().update({name: attr} for name, attr in new_attrs if isinstance(attr, DBOTField))

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


