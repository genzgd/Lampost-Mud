from __future__ import division
from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, DBOTField
from lampost.datastore.auto import RootAuto, TemplateField
from lampost.gameops.action import ActionError
from lampost.gameops.display import COMBAT_DISPLAY
from lampost.gameops.target import TargetClass
from lampost.lpflavor.attributes import POOL_LIST
from lampost.lpflavor.skill import BaseSkill, roll_calc, SkillTemplate, avg_calc
from lampost.mud.action import mud_action
from lampost.util.lmutil import args_print

m_requires('log', 'tools', 'dispatcher', __name__)

WEAPON_TYPES = {'sword': {'damage': 'slash', 'delivery': 'melee'},
                'axe': {'damage': 'slash', 'delivery': 'melee'},
                'mace': {'damage': 'blunt', 'delivery': 'melee'},
                'bow': {'damage': 'pierce', 'delivery': 'ranged'},
                'sling': {'damage': 'blunt', 'delivery': 'ranged'},
                'spear': {'damage': 'pierce', 'delivery': 'ranged'},
                'polearm': {'damage': 'pierce', 'delivery': 'melee'}}

WEAPON_OPTIONS = ['unused', 'unarmed', 'any'] + WEAPON_TYPES.keys()

DAMAGE_TYPES = {'weapon': {'desc': 'Use weapon damage type'},
                'blunt': {'desc': 'Blunt trauma (clubs, maces)'},
                'pierce': {'desc': 'Piercing damage (spears, arrows)'},
                'slash': {'desc': 'Slash damage (swords, knives)'},
                'cold': {'desc': 'Cold'},
                'fire': {'desc': 'Fire'},
                'shock': {'desc': 'Electric'},
                'acid': {'desc': 'Acid'},
                'poison': {'desc': 'Poison'},
                'psych': {'desc': 'Mental/psychic damage'},
                'spirit': {'desc': 'Spiritual damage'}}

DAMAGE_CATEGORIES = {'any': {'desc': 'All possible damage types', 'types': [damage_type for damage_type in DAMAGE_TYPES.iterkeys()]},
                     'physical': {'desc': 'All physical damage types', 'types': ['blunt', 'piece', 'slash']},
                     'elemental': {'desc': 'All elemental damage types', 'types': ['fire', 'shock', 'cold', 'acid', 'poison']}}

DEFENSE_DAMAGE_TYPES = DAMAGE_TYPES.copy()
DEFENSE_DAMAGE_TYPES.update(DAMAGE_CATEGORIES)

DAMAGE_DELIVERY = {'weapon': {'desc': 'Use weapon delivery type'},
                   'melee': {'desc': 'Delivered in hand to combat'},
                   'ranged': {'desc': 'Delivered via bow, spell, or equivalent'},
                   'psych': {'desc': 'Delivered via psychic or other non-physical means'}}

CON_LEVELS = ['Insignificant', 'Trivial', 'Pesky', 'Annoying', 'Irritating', 'Bothersome', 'Troublesome', 'Evenly Matched',
              'Threatening', 'Difficult', 'Intimidating', 'Imposing', 'Frightening', 'Terrifying', 'Unassailable']
CON_RANGE = int((len(CON_LEVELS) - 1) / 2)


def validate_weapon(ability, weapon_type):
    if not ability.weapon_type or ability.weapon_type == 'unused':
        return
    if ability.weapon_type == 'unarmed':
        if weapon_type:
            raise ActionError("You can't do that with a weapon.")
        return
    if not weapon_type:
        raise ActionError("That requires a weapon.")
    if ability.weapon_type != 'any' and ability.weapon_type != weapon_type:
        raise ActionError("You need a different weapon for that.")
    return True


def validate_delivery(ability, delivery):
    if delivery not in ability.delivery:
        raise ActionError("This doesn't work against that.")


def validate_dam_type(ability, damage_type):
    if damage_type not in ability.calc_damage_types:
        raise ActionError("That has no effect.")


def calc_consider(entity):
    try:
        best_attack = max([skill.points_per_pulse(entity) for skill in entity.skills.itervalues() if skill.template_id == 'attack'])
    except ValueError:
        best_attack = 0
    try:
        best_defense = max([skill.points_per_pulse(entity) for skill in entity.skills.itervalues() if skill.template_id == 'defense'])
    except ValueError:
        best_defense = 0
    pool_levels = sum(getattr(entity, base_pool_id, 0) for pool_id, base_pool_id in POOL_LIST)
    return int((best_attack + best_defense + pool_levels) / 2)


def consider_level(source_con, target_con):
    perc = max(target_con, 1) / max(source_con, 1) * 100
    perc = min(perc, 199)
    return int(perc / 13.27) - CON_RANGE


class Attack(RootAuto):

    success_map = TemplateField()
    fail_map = TemplateField()
    delivery = TemplateField()
    damage_pool = TemplateField()
    verb = TemplateField()

    def from_skill(self, skill, source):
        self.template = skill
        self.damage_type = skill.active_damage_type
        self.accuracy = roll_calc(source, skill.accuracy_calc, skill.skill_level)
        self.damage = roll_calc(source, skill.damage_calc, skill.skill_level)
        self.adj_damage = self.damage
        self.adj_accuracy = self.accuracy
        self.source = source
        return self

    def combat_log(self):
        return ''.join(['{n} ATTACK-- ',
                        args_print(damage_type=self.damage_type, accuracy=self.accuracy,
                                   damage=self.damage)])


class AttackTemplate(SkillTemplate):
    class_id = 'attack'
    dbo_set_key = 'attacks'


class AttackSkill(BaseSkill):
    template_id = 'attack'

    target_class = [TargetClass.ENV_LIVING]

    display = COMBAT_DISPLAY
    msg_class = 'rec_attack'
    damage_type = DBOTField('weapon')
    delivery = DBOTField('melee')
    damage_calc = DBOTField({})
    damage_pool = DBOTField('health')
    accuracy_calc = DBOTField({})
    weapon_type = DBOTField('any')
    prep_map = DBOTField({'s': 'You prepare to {v} {N}.', 't' : '{n} prepares to {v} you.', 'e': '{n} prepares to {v} {N}.'})
    success_map = DBOTField({'s': 'You {v} {N}.', 't': '{n} {v}s you.', 'e': '{n} {v}s {N}.', 'display': COMBAT_DISPLAY})
    fail_map = DBOTField({'s': 'You miss {N}.', 't': '{n} misses you.', 'e': '{n} missed {N}.', 'display': COMBAT_DISPLAY})

    def validate(self, source, target, **kwargs):
        if source == target:
            raise ActionError("You cannot harm yourself.  This is a happy place.")
        if validate_weapon(self, source.weapon_type):
            self.active_damage_type = source.weapon.damage_type
        else:
            self.active_damage_type = self.damage_type
        if 'dual_wield' in self.pre_reqs:
            validate_weapon(self, source.second_type)

    def prepare_action(self, source, target, **kwargs):
        self.validate(source, target, **kwargs)
        source.start_combat(target)
        target.start_combat(source)
        super(AttackSkill, self).prepare_action(source, target, **kwargs)

    def invoke(self, source, target_method, **ignored):
        attack = Attack().from_skill(self, source)
        combat_log(source, attack)
        target_method(source, attack)

    def points_per_pulse(self, owner):
        effect = avg_calc(owner, self.accuracy_calc, self.skill_level) + avg_calc(owner, self.damage_calc, self.skill_level)
        cost = avg_calc(owner, self.costs, self.skill_level)
        return int((effect - cost) / max(self.prep_time, 1))


class DefenseTemplate(SkillTemplate):
    class_id = 'defense'
    dbo_set_key = 'defenses'

    def on_loaded(self):
        super(DefenseTemplate, self).on_loaded()
        self.calc_damage_types = set()
        for damage_type in self.damage_type:
            try:
                self.calc_damage_types |= set(DAMAGE_CATEGORIES[damage_type]['types'])
            except KeyError:
                self.calc_damage_types.add(damage_type)


class DefenseSkill(BaseSkill):
    template_id = 'defense'

    target_class = [TargetClass.ENV_LIVING]
    damage_type = DBOTField(['physical'])
    delivery = DBOTField(['melee', 'ranged'])
    weapon_type = DBOTField('unused')
    absorb_calc = DBOTField({})
    avoid_calc = DBOTField({})
    success_map = DBOTField({'s': 'You avoid {N}\'s attack.', 't': '{n} avoids your attack.', 'e': '{n} avoids {N}\'s attack.'})
    calc_damage_types = TemplateField([])

    def invoke(self, source, **ignored):
        source.defenses.add(self)

    def revoke(self, source):
        if self in source.defenses:
            source.defenses.remove(self)

    def apply(self, owner, attack):
        try:
            validate_weapon(self, owner)
            validate_delivery(self, attack.delivery)
            validate_dam_type(self, attack.damage_type)
        except ActionError:
            return
        adj_accuracy = roll_calc(owner, self.avoid_calc, self.skill_level)
        combat_log(attack.source, lambda: ''.join(['{N} defense: ', self.name, ' adj_accuracy: ', str(adj_accuracy)]), self)
        attack.adj_accuracy -= adj_accuracy
        if attack.adj_accuracy < 0:
            return
        absorb = roll_calc(owner, self.absorb_calc, self.skill_level)
        combat_log(attack.source, lambda: ''.join(['{N} defense: ', self.name, ' absorb: ', str(absorb)]), self)
        attack.adj_damage -= absorb

    def points_per_pulse(self, owner):
        effect = avg_calc(owner, self.avoid_calc, self.skill_level) + avg_calc(owner, self.absorb_calc, self.skill_level)
        cost = avg_calc(owner, self.costs, self.skill_level)
        return int((effect - cost) / max(self.prep_time, 1))


@mud_action(('con', 'consider'), 'consider')
def consider(target_method, source, target, **ignored):
    target_con = target_method()
    source_con = source.rec_consider()
    con_string = CON_LEVELS[consider_level(source_con, target_con) + CON_RANGE]
    source.last_opponent = target
    source.status_change()
    return "At first glance, {} looks {}.".format(target.name, con_string)
