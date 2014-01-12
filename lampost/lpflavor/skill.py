from random import randint
from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.datastore.proto import ProtoField
from lampost.gameops.action import ActionError, convert_verbs
from lampost.gameops.template import Template, TemplateInstance
from lampost.model.entity import enhance_soul, diminish_soul
from lampost.mud.action import mud_action, imm_action

m_requires('log', 'datastore', 'dispatcher', __name__)


def add_skill(skill_id, target, skill_level):
    skill_template = load_object(SkillTemplate, skill_id)
    if not skill_template:
        warn("Skill {} not found.".format(skill_id))
        raise ActionError("Skill not found")
    skill_instance = skill_template.create_instance(target)
    skill_instance.skill_level = skill_level
    target.skills[skill_id] = skill_instance


def roll_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.viewitems())
    roll = randint(0, 20)
    if roll == 0:
        roll = -5
    if roll == 19:
        roll = 40
    return base_calc + roll * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


def avg_calc(source, calc, skill_level=0):
    base_calc = sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.viewitems())
    return base_calc + 10 * calc.get('roll', 0) + skill_level * calc.get('skill', 0)


class SkillTemplate(Template):
    dbo_key_type = 'skill'

    def on_loaded(self):
        super(SkillTemplate, self).on_loaded()
        if not self.auto_start:
            self.verbs = convert_verbs(self.verb)

    def config_instance(self, instance, owner):
        if getattr(owner, 'living', False):
            if self.auto_start:
                instance.invoke(owner)
            else:
                enhance_soul(owner, instance)

    @property
    def name(self):
        return self.template_id


class BaseSkill(TemplateInstance):
    dbo_key_type = 'skill'

    verb = DBOField()
    desc = DBOField()
    prep_time = DBOField(0)
    cool_down = DBOField(0)
    pre_reqs = DBOField([])
    costs = DBOField({})
    prep_map = DBOField({})
    display = DBOField('default')
    auto_start = DBOField(False)
    skill_level = DBOField(1)
    last_used = DBOField(0)
    verbs = ProtoField()
    name = ProtoField()

    def prepare_action(self, source, target, **kwargs):
        if not self.available:
            raise ActionError("You cannot {} yet.".format(self.verb))
        if self.prep_map and self.prep_time:
            source.broadcast(verb=self.verb, display=self.display, target=target, **self.prep_map)

    def use(self, source, **kwargs):
        source.apply_costs(self.costs)
        self.invoke(source, **kwargs)
        self.last_used = dispatcher.pulse_count

    def revoke(self, source):
        if not self.auto_start:
            diminish_soul(source, self)

    @property
    def available(self):
        return dispatcher.pulse_count - self.last_used >= self.cool_down

    def __call__(self, source, **kwargs):
        self.use(source, **kwargs)


@mud_action("skills", "has_skills", self_target=True)
def skills(source, target, **ignored):
    source.display_line("{}'s Skills:".format(target.name))

    for skill_id, skill in target.skills.iteritems():
        source.display_line("{}:   Level: {}".format(skill.verb if skill.verb else skill.name, str(skill.skill_level)))
        source.display_line("--{}".format(skill.desc if skill.desc else 'No Description'))


@imm_action("add skill", "args", prep="to", obj_msg_class="has_skills", self_object=True)
def add_skill_action(target, obj, **ignored):
    skill_id = target[0]
    try:
        skill_level = int(target[1])
    except IndexError:
        skill_level = 1
    add_skill(skill_id, obj, skill_level)
    return "Added {} to {}".format(target, obj.name)


@imm_action("remove skill", "args", prep="from", obj_msg_class="has_skills", self_object=True)
def remove_skill(target, obj, **ignored):
    try:
        existing_skill = obj.skills[target[0]]
    except KeyError:
        return "{} does not have that skill".format(obj.name)
    existing_skill.revoke(obj)
    del obj.skills[target[0]]
    if getattr(obj, 'dbo_id', None):
        save_object(obj)
    return "Removed {} from {}".format(target, obj.name)
