import sys

from random import randint
from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.datastore.dbo import RootDBO, DBORef
from lampost.gameops.action import make_action, ActionError
from lampost.gameops.template import template_class, Template, TemplateInstance
from lampost.mud.action import imm_actions, mud_action, imm_action

m_requires('log', 'datastore', 'dispatcher', __name__)


def roll_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.iteritems())
    roll = randint(0, 20)
    if roll == 0:
        roll = -5
    if roll == 19:
        roll = 40
    return base_calc + roll * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


class SkillTemplate(Template, RootDBO):
    dbo_fields = 'class_id',
    dbo_key_type = 'skill'

    def on_loaded(self):
        super(SkillTemplate, self).on_loaded()
        if not self.instance_cls.auto_start:
            make_action(self.instance_cls, self.instance_cls.verb)

    def config_instance(self, instance, owner):
        if instance.auto_start:
            instance.invoke(owner)
        else:
            owner.enhance_soul(instance)


class BaseSkill(TemplateInstance):
    dbo_fields = 'skill_level', 'last_used'
    template_fields = 'verb', 'desc', 'costs', 'pre_reqs', 'prep_time', \
                      'cool_down', 'prep_map', 'success_map', 'fail_map', 'auto_start'
    verb = None
    desc = None
    dbo_rev = 0
    prep_time = 0
    cool_down = 0
    pre_reqs = []
    costs = {}
    prep_map = {}
    success_map = {}
    fail_map = {}
    display = 'default'
    auto_start = False
    skill_level = 1
    last_used = 0

    def prepare_action(self, source, target, **kwargs):
        if self.cool_down and self.last_used + self.cool_down > dispatcher.pulse_count:
            raise ActionError("You cannot {} yet.".format(self.verb))
        if self.prep_map:
            source.broadcast(display=self.display, target=target, **self.prep_map)

    def use(self, source, **kwargs):
        source.apply_costs(self.costs)
        self.invoke(source, **kwargs)
        self.last_used = dispatcher.pulse_count

    def __call__(self, source, **kwargs):
        self.use(source, **kwargs)


@mud_action("skills", "has_skills", self_target=True)
def skills(source, target, **ignored):
    source.display_line("{}'s Skills:".format(target.name))

    for skill_id, skill_status in target.skills.iteritems():
        skill = skill_service.skills.get(skill_id)
        if skill:
            source.display_line("{}:   Level: {}".format(skill.verb if skill.verb else skill.dbo_id, str(skill_status.skill_level)))
            source.display_line("--{}".format(skill.desc))
        else:
            warn("{} has missing skill {} ".format(target.name, skill_id))


@imm_action("add skill", "args", prep="to", obj_msg_class="has_skills", self_object=True)
def add_skill(target, obj, **ignored):
    skill_id = target[0]
    try:
        skill_level = int(target[1])
    except IndexError:
        skill_level = 1

    skill_template = load_object(SkillTemplate, skill_id)
    if not skill_template:
        return "Skill Id {} NOT FOUND".format(skill_id)
    skill_instance = skill_template.create_instance(obj)
    skill_instance.skill_level = skill_level
    obj.append_map('skills', skill_instance)
    return "Added {} to {}".format(target, obj.name)


@imm_action("remove skill", "args", prep="from", obj_msg_class="has_skills", self_object=True)
def remove_skill(target, obj, **ignored):
    skill_service.remove_skill(target[0], obj)
    return "Removed {} from {}".format(target, obj.name)


