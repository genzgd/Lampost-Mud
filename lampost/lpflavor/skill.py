import sys

from random import randint
from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import make_action, ActionError
from lampost.mud.action import imm_actions, mud_action, imm_action

m_requires('log', 'datastore', 'dispatcher', 'skill_service', __name__)

SKILL_TYPES = []


def base_skill(cls):
    SKILL_TYPES.append(cls)
    return cls


def roll_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.iteritems())
    roll = randint(0, 20)
    if roll == 0:
        roll = -5
    if roll == 19:
        roll = 40
    return base_calc + roll * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


@provides('skill_service')
class SkillService(object):

    def _post_init(self):
        register('player_baptise', self._baptise, priority=200)
        register('mobile_baptise', self._baptise, priority=200)
        self.skills = {}
        for skill_type in SKILL_TYPES:
            self.skills.update({skill_id: load_object(skill_type, skill_id) for skill_id in fetch_set_keys(skill_type.dbo_set_key)})

    def add_skill(self, skill_id, entity):
        try:
            skill = self.skills[skill_id]
            if skill.auto_start:
                skill.invoke(entity)
            else:
                entity.enhance_soul(skill)
        except KeyError:
            log.warn("No global skill {} found for entity {}".format(skill_id, entity.name))

    def remove_skill(self, skill_id, entity):
        try:
            skill = self.skills[skill_id]
            if skill.auto_start:
                skill.revoke(entity)
            else:
                entity.diminish_soul(skill)
        except KeyError:
            log.warn("No global skill {} found for entity {}".format(skill_id, entity.name))

    def _baptise(self, entity):
        for skill_id in entity.skills.iterkeys():
            self.add_skill(skill_id, entity)


class SkillStatus(RootDBO):
    dbo_fields = 'skill_level', 'last_used'
    last_used = 0
    skill_level = 1


class BaseSkill():
    dbo_fields = 'dbo_rev', 'verb', 'desc', 'costs', 'pre_reqs', 'prep_time',\
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
    weapon_type = None

    def on_loaded(self):
        if not self.auto_start and self.verb:
            make_action(self, self.verb)

    def prepare_action(self, source, target, **kwargs):
        skill_status = source.skills[self.dbo_id]
        if self.cool_down and skill_status.last_used + self.cool_down > dispatcher.pulse_count:
            raise ActionError("You cannot {} yet.".format(self.verb))
        if self.prep_map:
            source.broadcast(display=self.display, target=target, **self.prep_map)

    def use(self, source, **kwargs):
        source.apply_costs(self.costs)
        skill_status = source.skills.get(self.dbo_id)
        self.invoke(skill_status, source, **kwargs)
        skill_status.last_used = dispatcher.pulse_count

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
    skill_service.add_skill(skill_id, obj)
    skill_status = SkillStatus()
    skill_status.level = skill_level
    try:
        obj.append_map('skills', skill_status, skill_id)
    except AttributeError:
        obj.skills[skill_id] = skill_status
    return "Added {} to {}".format(target, obj.name)


@imm_action("remove skill", "args", prep="from", obj_msg_class="has_skills", self_object=True)
def remove_skill(target, obj, **ignored):
    skill_service.remove_skill(target[0], obj)
    return "Removed {} from {}".format(target, obj.name)


