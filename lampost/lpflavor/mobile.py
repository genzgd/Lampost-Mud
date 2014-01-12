from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.lpflavor.archetype import Archetype
from lampost.lpflavor.attributes import fill_pools
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillTemplate
from lampost.model.mobile import Mobile, MobileTemplate
from lampost.model.race import base_attr_value

m_requires('log', 'datastore', 'dispatcher', __name__)


class MobileLP(Mobile, EntityLP):
    archetype = DBOField()
    level = DBOField(1)


class MobileTemplateLP(MobileTemplate):
    default_skills = DBOField({})

    def on_loaded(self):
        if self.archetype:
            arch = load_object(Archetype, self.archetype)
            for attr_name, start_value in arch.base_attrs.iteritems():
                setattr(instance_cls, attr_name, start_value)
            self.desc = arch.desc
        else:
            for attr_name in Archetype.attr_list:
                setattr(self.instance_cls, attr_name, base_attr_value * self.level)
        super(MobileTemplateLP, self).on_loaded()

    def config_instance(self, mobile, owner):
        mobile.skills = {}
        for skill_id, skill_status in self.default_skills.iteritems():
            skill_template = load_object(SkillTemplate, skill_id)
            if not skill_template:
                warn("Skill {} not found.".format(skill_id))
                continue
            skill_instance = skill_template.create_instance(mobile)
            skill_instance.skill_level = skill_status['skill_level']
            mobile.skills[skill_id] = skill_instance
        fill_pools(mobile)
        mobile.inven = set()
        mobile.baptise()
