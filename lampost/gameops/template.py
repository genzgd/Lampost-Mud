from lampost.context.resource import m_requires
from lampost.datastore.auto import TemplateField
from lampost.datastore.dbo import DBOField, RootDBO

m_requires('log', 'cls_registry', 'datastore', __name__)


def template_class(template_cls, instance_cls):
    template_cls = cls_registry(template_cls)
    instance_cls = cls_registry(instance_cls)
    template_cls.instance_cls = instance_cls
    template_cls.add_dbo_fields({name: dbo_field for name, dbo_field in instance_cls.dbo_fields.viewitems() if isinstance(dbo_field, TemplateField)})
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


class TemplateInstance(RootDBO):

    @classmethod
    def load_ref(cls, dto_repr, owner=None):
        if hasattr(cls, 'template_cls'):
            try:
                template = load_object(cls.template_cls, dto_repr['template_id'])
                instance = template.create_instance(owner)
            except KeyError:
                warn("Missing template_id loading template {}".format(dto_repr))
                return None
        else:
            instance = cls()
        instance.hydrate(dto_repr)
        try:
            instance.on_created()
        except AttributeError:
            pass
        return instance

    @property
    def save_value(self):
        return self.metafields(super(TemplateInstance, self).save_value, ['template_id'])
