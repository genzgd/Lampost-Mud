from random import randint
from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, DBOTField
from lampost.datastore.auto import TemplateField
from lampost.gameops.action import ActionError, convert_verbs
from lampost.gameops.template import Template, TemplateInstance
from lampost.mud.action import mud_action, imm_action

m_requires(__name__, 'log', 'datastore', 'dispatcher')


def add_skill(skill_id, target, skill_level):
    skill_template = load_object(SkillTemplate, skill_id)
    if not skill_template:
        warn("Skill {} not found.", skill_id)
        raise ActionError("Skill not found")
    skill_instance = skill_template.create_instance(target)
    skill_instance.skill_level = skill_level
    target.add_skill(skill_instance)


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


class SkillTemplate(Template):
    dbo_key_type = 'skill'
    dbo_set_key = 'skills'

    def on_loaded(self):
        if not self.auto_start:
            self.verbs = convert_verbs(self.verb)

    @property
    def name(self):
        return self.template_id


class BaseSkill(TemplateInstance):
    template_id = 'skill'

    verb = DBOTField()
    desc = DBOTField()
    prep_time = DBOTField(0)
    cool_down = DBOTField(0)
    pre_reqs = DBOTField([])
    costs = DBOTField({})
    prep_map = DBOTField({})
    display = DBOTField('default')
    auto_start = DBOTField(False)
    skill_level = DBOField(1)
    last_used = DBOField(0)
    verbs = TemplateField()
    name = TemplateField()

    def prepare_action(self, source, target, **kwargs):
        if self.available > 0:
            raise ActionError("You cannot {} yet.".format(self.verb))
        self.validate(source, target, **kwargs)
        if self.prep_map and self.prep_time:
            source.broadcast(verb=self.verb, display=self.display, target=target, **self.prep_map)

    def validate(self, source, target, **kwargs):
        pass

    def use(self, source, **kwargs):
        source.apply_costs(self.costs)
        self.invoke(source, **kwargs)
        self.last_used = current_pulse()

    def invoke(self, source, **_):
        pass

    def revoke(self, source):
        pass

    @property
    def available(self):
        return self.last_used + self.cool_down - current_pulse()

    def __call__(self, source, **kwargs):
        self.use(source, **kwargs)


@mud_action("skills", "skills", self_target=True)
def skills(source, target, **_):
    source.display_line("{}'s Skills:".format(target.name))

    for skill_id, skill in target.skills.items():
        source.display_line("{}:   Level: {}".format(skill.verb if skill.verb else skill.name, str(skill.skill_level)))
        source.display_line("--{}".format(skill.desc if skill.desc else 'No Description'))


@imm_action("add skill", target_class="args", prep="to", obj_msg_class="skills", self_object=True)
def add_skill_action(target, obj, **_):
    try:
        skill_id = target[0]
    except IndexError:
        raise ActionError("Skill id required")
    try:
        skill_level = int(target[1])
    except IndexError:
        skill_level = 1
    add_skill(skill_id, obj, skill_level)
    if getattr(obj, 'dbo_id', None):
        save_object(obj)
    return "Added {} to {}".format(target, obj.name)


@imm_action("remove skill", target_class="args", prep="from", obj_msg_class="skills", self_object=True)
def remove_skill(target, obj, **_):
    obj.remove_skill(target[0])
    if getattr(obj, 'dbo_id', None):
        save_object(obj)
    return "Removed {} from {}".format(target, obj.name)
