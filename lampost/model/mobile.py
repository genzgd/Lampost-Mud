from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.template import Template
from lampost.model.entity import Entity
from lampost.model.item import target_keys


class MobileTemplate(Template):
    dbo_key_type = "mobile"

    @property
    def dbo_set_key(self):
        return "area_mobiles:{}".format(self.area_id)

    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]

    def config_instance(self, instance, room):
        instance.baptise()
        instance.original_env = room
        room.mobiles[self].add(instance)

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.dbo_id)

    def on_loaded(self):
        self.target_keys = target_keys(self)
        super(MobileTemplate, self).on_loaded()


class Mobile(Entity):
    template_id = 'mobile'

    def detach(self):
        super(Mobile, self).detach()
        self.original_env.mobiles[self.template].remove(self)


class MobileReset(RootDBO):
    class_id = 'mobile_reset'
    mobile_id = DBOField()
    reset_count = DBOField(1)
    reset_max = DBOField(1)
    article_loads = DBOField([], 'article_load')

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.mobile_id)
