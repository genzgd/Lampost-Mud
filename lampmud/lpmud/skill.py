from random import randint

from lampost.di.resource import Injected, module_inject
from lampost.meta.auto import TemplateField
from lampost.db.registry import dbo_types
from lampost.db.dbo import CoreDBO, KeyDBO, OwnerDBO
from lampost.db.dbofield import DBOField, DBOTField
from lampost.db.template import Template, TemplateInstance
from lampost.gameops.action import ActionError

from lampmud.mud.action import mud_action, imm_action

log = Injected('log')
db = Injected('datastore')
ev = Injected('dispatcher')
module_inject(__name__)


def add_skill(skill_template, target, skill_level, skill_source=None):
    if skill_template:
        skill_instance = skill_template.create_instance(target)
        skill_instance.skill_level = skill_level
        skill_instance.skill_source = skill_source
        target.add_skill(skill_instance)
        return skill_instance
    log.warn('Unable to add missing skill {}', skill_template.dbo_id)


def roll_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.items())
    roll = randint(0, 20)
    if roll == 0:
        roll = -5
    if roll == 19:
        roll = 40
    return base_calc + roll * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


def avg_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.items())
    return base_calc + 10 * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


class SkillTemplate(KeyDBO, OwnerDBO, Template):
    def _on_loaded(self):
        if not self.auto_start:
            self.verbs = self.verb


class DefaultSkill(CoreDBO):
    class_id = 'default_skill'
    skill_template = DBOField(dbo_class_id='untyped', required=True)
    skill_level = DBOField(1)


class BaseSkill(TemplateInstance):
    verb = DBOTField()
    name = DBOTField()
    desc = DBOTField()
    prep_time = DBOTField(0)
    cool_down = DBOTField(0)
    pre_reqs = DBOTField([])
    costs = DBOTField({})
    prep_map = DBOTField({})
    display = DBOTField('default')
    auto_start = DBOTField(False)
    skill_level = DBOField(1)
    skill_source = DBOField()
    last_used = DBOField(0)
    verbs = TemplateField()

    def prepare_action(self, source, target):
        if self.available > 0:
            raise ActionError("You cannot {} yet.".format(self.verb))
        self.validate(source, target)
        if self.prep_map and self.prep_time:
            source.broadcast(verb=self.verb, display=self.display, target=target, **self.prep_map)

    def validate(self, source, target, **kwargs):
        pass

    def use(self, source, **kwargs):
        source.apply_costs(self.costs)
        self.invoke(source, **kwargs)
        self.last_used = ev.current_pulse

    def invoke(self, source, **kwargs):
        pass

    def revoke(self, source):
        pass

    @property
    def available(self):
        return self.last_used + self.cool_down - ev.current_pulse

    def __call__(self, source, **kwargs):
        self.use(source, **kwargs)


@mud_action("skills", "skills", target_class="living")
def skills(source, target):
    source.display_line("{}'s Skills:".format(target.name))

    for skill_id, skill in target.skills.items():
        source.display_line("{}:   Level: {}".format(skill.name, str(skill.skill_level)))
        source.display_line("--{}".format(skill.desc if skill.desc else 'No Description'))


@imm_action("add skill", target_class="target_str", prep="to", obj_msg_class="skills", obj_class="living", self_object=True)
def add_skill_action(target, obj):
    skill_args = target.split(' ')
    try:
        skill_name = skill_args[0]
    except IndexError:
        raise ActionError("Skill name required")
    try:
        skill_level = int(skill_args[1])
    except (IndexError, ValueError):
        skill_level = 1
    if ':' in skill_name:
        skill_id = skill_name
    else:
        skill_id = None
        for skill_type in dbo_types(SkillTemplate):
            if skill_name in db.fetch_set_keys(skill_type.dbo_set_key):
                skill_id = '{}:{}'.format(skill_type.dbo_key_type, skill_name)
                break
    if skill_id:
        skill_template = db.load_object(skill_id)
        if skill_template:
            add_skill(skill_template, obj, skill_level, 'immortal')
            if getattr(obj, 'dbo_id', None):
                db.save_object(obj)
            return "Added {} to {}".format(skill_name, obj.name)
    return "Skill {} not found ".format(skill_name)


@imm_action("remove skill", target_class="target_str", prep="from", obj_msg_class="skills", obj_class="living", self_object=True)
def remove_skill(target, obj):
    if ':' in target:
        skill_id = target
    else:
        skill_id = None
        for skill_type in dbo_types(SkillTemplate):
            skill_id = '{}:{}'.format(skill_type.dbo_key_type, target)
            if skill_id in obj.skills:
                break
            else:
                skill_id = None
    obj.remove_skill(skill_id)
    if getattr(obj, 'dbo_id', None):
        db.save_object(obj)
    return "Removed {} from {}".format(target, obj.name)
