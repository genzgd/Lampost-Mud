from collections import defaultdict
from lampost.context.resource import m_requires
from lampost.lpflavor.archetype import Archetype
from lampost.lpflavor.attributes import fill_pools
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillStatus
from lampost.model.mobile import Mobile, MobileTemplate

m_requires('log', 'dispatcher', __name__)


class MobileLP(Mobile, EntityLP):
    template_fields = 'archetype', 'level', 'skills'

    archetype = None
    level = 1
    skills = {}


def config_instance_cls(self):

    if self.archetype:
        arch = load_object(Archetype, self.archetype)
        for attr_name, start_value in arch.base_attrs.iteritems():
            setattr(self.instance_cls, attr_name, start_value)
        self.desc = arch.desc
    else:
        for attr_name in Archetype.attr_list:
            setattr(self.instance_cls, attr_name, Archetype.base_attr_value * self.level)
    self.instance_cls.soul = defaultdict(set)
    self.instance_cls.defenses = []
    dispatch('mobile_baptise', self.instance_cls)


def config_instance(self, mobile):
    mobile_skills = {}
    for skill_id, skill_specs in self.instance_cls.skills.iteritems():
        skill_status = SkillStatus()
        skill_status.level = skill_specs.get('level')
        mobile_skills[skill_id] = skill_status
    fill_pools(mobile)
    mobile.baptise()
    mobile.equip(set())

MobileTemplate.config_instance_cls = config_instance_cls
MobileTemplate.config_instance = config_instance

