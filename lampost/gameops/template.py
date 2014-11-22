from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO

m_requires(__name__, 'log', 'datastore')


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


class TemplateInstance(RootDBO):
    @classmethod
    def load_ref(cls, dbo_repr, owner=None):
        if hasattr(cls, 'template_id'):
            try:
                template = load_by_key(cls.template_id, dbo_repr['template_id'])
                instance = template.create_instance(owner)
            except KeyError:
                warn("Missing template_id loading template {}", dbo_repr)
                return None
            except AttributeError:
                warn("Missing database template loading template {}", dbo_repr)
                return None
        else:
            instance = cls()
        instance.hydrate(dbo_repr)
        try:
            instance.on_created()
        except AttributeError:
            pass
        return instance

    @property
    def save_value(self):
        return self.metafields(super().save_value, ['template_id'])
