from lampost.datastore.meta import CommonMeta


class Template(metaclass=CommonMeta):

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.template = self
        instance.template_key = self.dbo_key
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass