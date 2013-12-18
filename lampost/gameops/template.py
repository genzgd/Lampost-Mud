from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, RootDBOMeta
from lampost.util.lmutil import cls_name

m_requires('cls_registry', __name__)


def template_class(template_cls, instance_cls):
    instance_cls = cls_registry(instance_cls)
    template_fields = set()

    def add_fields(child_cls):
        for field in getattr(child_cls, 'template_fields', ()):
            if hasattr(child_cls, field) and not hasattr(template_cls, field):
                setattr(template_cls, field, getattr(child_cls, field))
            template_fields.add(field)
        for base_cls in child_cls.__bases__:
            add_fields(base_cls)

    add_fields(instance_cls)

    template_cls.template_fields = template_fields
    template_cls.dbo_fields.update(template_fields)
    template_cls.instance_base = instance_cls


class TemplateException(Exception):
    pass


class Template():
    dbo_fields = "dbo_rev", "world_max"
    instance_count = 0
    world_max = 1000000
    dbo_rev = 0

    def config_instance(self, instance):
        pass

    def config_instance_cls(self):
        pass

    def create_instance(self):
        if self.instance_count >= self.world_max:
            raise TemplateException
        instance = self.instance_cls()
        instance.on_loaded()
        self.instance_count += 1
        self.config_instance(instance)
        return instance

    def delete_instance(self, instance):
        self.instance_count -= 1

    def on_loaded(self):
        attrs = {name: getattr(self, name) for name in self.template_fields}
        attrs['template'] = self
        self.instance_cls = type.__new__(type, str(self.dbo_id), (self.instance_base,), attrs)
        self.config_instance_cls()




