from collections import defaultdict
from lampost.context.resource import m_requires
from lampost.lpflavor.archetype import Archetype
from lampost.lpflavor.attributes import fill_pools
from lampost.lpflavor.entity import EntityLP
from lampost.model.item import config_targets
from lampost.model.mobile import Mobile, MobileTemplate
from lampost.model.race import base_attr_value

m_requires('log', 'dispatcher', __name__)


class MobileLP(Mobile, EntityLP):
    template_fields = 'archetype', 'level'
    archetype = None
    level = 1


def config_instance_cls(self, instance_cls):
    config_targets(instance_cls)
    if self.archetype:
        arch = load_object(Archetype, self.archetype)
        for attr_name, start_value in arch.base_attrs.iteritems():
            setattr(instance_cls, attr_name, start_value)
        self.desc = arch.desc
    else:
        for attr_name in Archetype.attr_list:
            setattr(instance_cls, attr_name, base_attr_value * self.level)
    instance_cls.soul = defaultdict(set)
    dispatch('mobile_baptise', instance_cls)


def config_instance(self, mobile, owner=None):
    fill_pools(mobile)
    mobile.baptise()
    mobile.equip(set())

MobileTemplate.config_instance_cls = config_instance_cls
MobileTemplate.config_instance = config_instance

