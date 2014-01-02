from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO

m_requires('cls_registry', 'datastore', __name__)


def template_class(template_cls, instance_cls):
    template_cls = cls_registry(template_cls)
    instance_cls = cls_registry(instance_cls)
    template_cls.instance_cls = instance_cls
    template_cls.add_dbo_fields(instance_cls.dbo_fields)


class Template(RootDBO):
    dbo_rev = DBOField(0)

    @classmethod
    def load_ref(cls, dbo_id, owner=None):
        template = load_object(cls, dbo_id)
        return template.create_instance(owner)

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.prototype = self
        instance.dbo_id = self.dbo_id
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass

    def on_loaded(self):
        try:
            self.instance_cls.config_prototype(self)
        except AttributeError:
            pass
