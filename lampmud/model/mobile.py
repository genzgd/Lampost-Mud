from lampost.db.dbo import CoreDBO, ChildDBO
from lampost.db.dbofield import DBOField
from lampost.db.template import Template

from lampmud.model.entity import Entity
from lampmud.model.item import target_keys, ItemInstance


class MobileTemplate(ChildDBO, Template):
    dbo_key_type = 'mobile'
    dbo_parent_type = 'area'

    def _on_loaded(self):
        self.target_keys = target_keys(self)

    def config_instance(self, instance, room):
        instance.attach()
        instance.original_env = room
        room.mobiles[self].add(instance)
        instance.enter_env(room)


class Mobile(Entity, ItemInstance):
    template_id = 'mobile'

    def _on_detach(self):
        self.original_env.mobiles[self.template].remove(self)


class MobileReset(CoreDBO):
    class_id = 'mobile_reset'
    mobile = DBOField(dbo_class_id='mobile', required=True)
    reset_key = DBOField(0)
    reset_count = DBOField(1)
    reset_max = DBOField(1)
