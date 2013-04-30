from lampost.lpflavor.archetype import Archetype
from lampost.lpflavor.attributes import fill_pools
from lampost.lpflavor.entity import EntityLP
from lampost.model.mobile import Mobile, MobileTemplate


class MobileLP(Mobile, EntityLP):
    dbo_fields = EntityLP.dbo_fields + ('archetype', 'level')
    level = 0
    archetype = None


def config_instance(self, mobile):
    if mobile.archetype:
        arch = load_object(Archetype, self.archetype)
        for attr_name, start_value in arch.base_attrs.iteritems():
            setattr(mobile, attr_name, start_value)
        self.desc = arch.desc
    else:
        for attr_name in Archetype.attr_list:
            setattr(mobile, attr_name, Archetype.base_attr_value * mobile.level)
    fill_pools(mobile)
    mobile.baptise(set())
    mobile.equip(set())

MobileTemplate.config_instance = config_instance
