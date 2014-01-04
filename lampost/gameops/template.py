from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO

m_requires('cls_registry', 'datastore', __name__)


def template_class(template_cls, instance_cls):
    template_cls = cls_registry(template_cls)
    instance_cls = cls_registry(instance_cls)
    template_cls.instance_cls = instance_cls
    template_cls.add_dbo_fields(instance_cls.dbo_fields)
    instance_cls.dbo_key_type = template_cls.dbo_key_type


class Template(RootDBO):
    dbo_rev = DBOField(0)

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.template = self
        instance.template_id = self.dbo_id
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass

    def on_loaded(self):
        try:
            self.instance_cls.config_template(self)
        except AttributeError:
            pass


class TemplateInstance(RootDBO):

    @classmethod
    def load_ref(cls, dto_repr, owner=None):
        try:
            template = load_object(cls, dto_repr['template_id'])
            return template.create_instance(owner).hydrate(dto_repr)
        except KeyError:
            return cls().hydrate(dto_repr)





