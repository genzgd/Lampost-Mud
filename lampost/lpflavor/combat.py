from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import ActionError
from lampost.lpflavor.skill import base_skill, BaseSkill

m_requires('log', 'dispatcher', __name__)

DAMAGE_TYPES = {'blunt': {'desc': 'Blunt trauma (clubs, maces)'},
                'pierce': {'desc': 'Piercing damage (spears, arrows)'},
                'slash': {'desc': 'Slash damage (swords, knives)'},
                'cold': {'desc': 'Cold'},
                'fire': {'desc': 'Fire'},
                'shock': {'desc': 'Electric'},
                'acid': {'desc': 'Acid'},
                'poison': {'desc': 'Poison'},
                'psych': {'desc': 'Mental/psychic damage'},
                'spirit': {'desc': 'Spiritual damage'}}


class Attack(object):
    def __init__(self, skill, skill_level, source):
        self.damage_type = skill.damage_type
        self.accuracy = skill.calc_accuracy(source) * skill_level
        self.damage = skill.calc_damage(source) * skill_level
        self.damage_pool = skill.damage_pool


@base_skill()
class AttackSkill(BaseSkill, RootDBO):
    dbo_fields = BaseSkill.dbo_fields + ('damage_type', 'damage_calc', 'accuracy_calc', 'weapon_type')
    dbo_key_type = 'skill'
    dbo_set_key = 'skill_attack'

    msg_class = 'attack'
    damage_type = 'weapon'
    damage_calc = {}
    damage_pool = 'health'
    accuracy_calc = {}
    weapon_type = 'unused'

    def prepare_action(self, source, target, **kwargs):
        if source == target:
            raise ActionError("You cannot harm yourself.  This is a happy place.")
        self._validate_weapon(source.weapon_type)
        if 'dual_wield' in self.pre_reqs:
            self._validate_weapon(source.second_type)
        super(AttackSkill, self).prepare_action(source, target, **kwargs)

    def _validate_weapon(self, weapon_type):
        if self.weapon_type == 'unused':
            return
        if self.weapon_type == 'unarmed':
            if weapon_type:
                raise ActionError("You can't do that with a weapon.")
            return
        if not weapon_type:
            raise ActionError("That requires a weapon.")
        if self.weapon_type != 'any' and self.weapon_type != source.weapon:
            raise ActionError("You need a different weapon for that.")

    def invoke(self, skill_status, source, target_method, **ignored):
        attack = Attack(self, skill_status.skill_level, source)
        target_method(source, attack)

    def calc_damage(self, source):
        return sum(getattr(source, attr, 0) * damage for attr, damage in self.damage_calc.iteritems())

    def calc_accuracy(self, source):
        return sum(getattr(source, attr, 0) * accuracy for attr, accuracy in self.accuracy_calc.iteritems())











