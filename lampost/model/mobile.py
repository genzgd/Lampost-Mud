from lampost.datastore.dbo import CoreDBO, ChildDBO
from lampost.datastore.dbofield import DBOField
from lampost.gameops.template import Template
from lampost.model.entity import Entity
from lampost.model.item import target_keys, BaseTemplate


class MobileTemplate(ChildDBO, Template):
    dbo_key_type = "mobile"
    dbo_parent_type = "area"

    def config_instance(self, instance, room):
        instance.baptise()
        instance.original_env = room
        room.mobiles[self].add(instance)
        instance.enter_env(room)

    def on_loaded(self):
        self.target_keys = target_keys(self)


class Mobile(Entity, BaseTemplate):
    template_id = 'mobile'

    def on_detach(self):
        self.original_env.mobiles[self.template].remove(self)


class MobileReset(CoreDBO):
    class_id = 'mobile_reset'
    mobile = DBOField(dbo_class_id='mobile', required=True)
    reset_key = DBOField(0)
    reset_count = DBOField(1)
    reset_max = DBOField(1)