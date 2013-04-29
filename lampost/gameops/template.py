from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO
from lampost.util.lmutil import cls_name

m_requires('cls_registry', __name__)


class TemplateException(Exception):
    pass


class Template(RootDBO):
    dbo_fields = ("dbo_rev", "instance_class", "world_max")
    instance_count = 0
    world_max = 1000000
    dbo_rev = 0

    @classmethod
    def template_class(cls, template_cls):
        cls.template_fields = template_cls.dbo_fields
        cls.dbo_fields = Template.dbo_fields + cls.template_fields
        cls.instance_class = cls_name(template_cls)

    def config_instance(self, instance):
        pass

    def create_instance(self):
        if self.instance_count >= self.world_max:
            raise TemplateException
        instance = cls_registry(self.instance_class)()
        for field in self.template_fields:
            setattr(instance, field, getattr(self, field, None))
        instance.on_loaded()
        instance.template = self
        self.instance_count += 1
        self.config_instance(instance)
        return instance

    def delete_instance(self, instance):
        self.instance_count -= 1