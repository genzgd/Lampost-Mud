from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.template import Template
from lampost.model.entity import Entity
from lampost.model.item import target_keys


class MobileTemplate(Template):
    dbo_key_type = "mobile"
    dbo_parent_type = "area"

    def config_instance(self, instance, room):
        instance.baptise()
        instance.original_env = room
        room.mobiles[self].add(instance)

    def on_loaded(self):
        self.target_keys = target_keys(self)


class Mobile(Entity):
    template_id = 'mobile'

    def detach(self):
        super().detach()
        self.original_env.mobiles[self.template].remove(self)


class MobileReset(RootDBO):
    class_id = 'mobile_reset'
    mobile_id = DBOField(None, 'mobile', True)
    reset_count = DBOField(1)
    reset_max = DBOField(1)
    article_loads = DBOField([], 'article_load')

