from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO

m_requires(__name__, 'datastore')


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