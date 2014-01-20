from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.gameops.template import Template, TemplateInstance
from lampost.model.item import BaseItem


m_requires('cls_registry', __name__)


class FeatureTemplate(Template):
    dbo_set_key = 'features'
    dbo_key_type = 'feature'

    instance_class_id = DBOField()

    def on_loaded(self):
        self.instance_cls = cls_registry(self.instance_class_id)

    def config_instance(self, instance, room):
        instance.room = room


class Feature(BaseItem):
    template_cls = FeatureTemplate
