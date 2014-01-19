from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO

m_requires('cls_registry', 'datastore', __name__)


def template_class(template_cls, instance_cls):
    template_cls = cls_registry(template_cls)
    instance_cls = cls_registry(instance_cls)
    template_cls.instance_cls = instance_cls
    template_cls.add_dbo_fields(instance_cls.dbo_fields)
    instance_cls.template_cls = template_cls


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
        self.template_id = self.dbo_id
        try:
            self.instance_cls.config_template(self)
        except AttributeError:
            pass


class TemplateInstance(RootDBO):

    @classmethod
    def load_ref(cls, dto_repr, owner=None):
        if hasattr(cls, 'template_cls'):
            template = load_object(cls.template_cls, dto_repr['template_id'])
            return template.create_instance(owner).hydrate(dto_repr)
        return cls().hydrate(dto_repr)

    @property
    def save_value(self):
        return self.metafields(super(TemplateInstance, self).save_value, ['template_id'])
