from lampost.datastore.dbo import DBOField, RootDBO


class Template(RootDBO):
    dbo_rev = DBOField(0)

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.template = self
        instance.template_key = self.dbo_key
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass