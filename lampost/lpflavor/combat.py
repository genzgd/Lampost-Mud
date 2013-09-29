from random import randint
from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import ActionError
from lampost.gameops.display import COMBAT_DISPLAY
from lampost.lpflavor.skill import base_skill, BaseSkill
from lampost.util.lmutil import args_print

m_requires('log', 'tools', 'dispatcher', __name__)

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

DAMAGE_DELIVERY = {'melee', 'ranged', 'psychic'}


def attr_calc(source, calc):
    return sum(getattr(source, attr, 0) * calc_value for attr, calc_value in calc.iteritems())


class Attack(object):
    def from_skill(self, skill, skill_level, source):
        self.success_map = skill.success_map
        self.fail_map = skill.fail_map
        self.damage_type = skill.damage_type
        self.accuracy = attr_calc(source, skill.accuracy_calc) * skill_level + randint(0, 50)
        self.damage = (attr_calc(source, skill.damage_calc) + randint(0, 20)) * skill_level
        self.damage_pool = skill.damage_pool
        self.adj_damage = self.damage
        self.adj_accuracy = self.accuracy
        self.delivery = skill.delivery
        return self

    def raw(self, damage, accuracy=100, damage_type='spirit', damage_pool='health'):
        self.__dict__.update(locals())
        return self

    def combat_log(self):
        return ''.join(['{n} ATTACK-- ',
                        args_print(damage_type=self.damage_type, accuracy=self.accuracy,
                                   damage=self.damage)])


@base_skill
class AttackSkill(BaseSkill, RootDBO):
    dbo_fields = BaseSkill.dbo_fields + ('damage_type', 'damage_calc', 'accuracy_calc', 'weapon_type')
    dbo_key_type = 'skill'
    dbo_set_key = 'skill_attack'

    msg_class = 'attack'
    damage_type = 'blunt'
    delivery = 'melee'
    damage_calc = {}
    damage_pool = 'health'
    accuracy_calc = {}
    weapon_type = None
    success_map = {'s': 'You hit {N}.', 't': '{n} hits you.', 'e': '{n} hits {N}.', 'display': COMBAT_DISPLAY}
    fail_map = {'s': 'You miss {N}.', 't': '{n} misses you.', 'e': '{n} missed {N}.', 'display': COMBAT_DISPLAY}

    def prepare_action(self, source, target, **kwargs):
        if source == target:
            raise ActionError("You cannot harm yourself.  This is a happy place.")
        self._validate_weapon(source.weapon_type)
        if 'dual_wield' in self.pre_reqs:
            self._validate_weapon(source.second_type)
        super(AttackSkill, self).prepare_action(source, target, **kwargs)

    def invoke(self, skill_status, source, target_method, **ignored):
        attack = Attack().from_skill(self, skill_status.skill_level, source)
        combat_log(source, attack)
        target_method(source, attack)


@base_skill
class DefenseSkill(BaseSkill, RootDBO):
    dbo_fields = BaseSkill.dbo_fields + ('damage_type', 'absorb_calc', 'accuracy_calc', 'weapon_type')
    dbo_key_type = 'skill'
    dbo_set_key = 'skill_defense'

    damage_type = 'any'
    delivery = 'melee'
    weapon_type = 'unused'
    accuracy_calc = {}
    absorb_calc = {}
    success_map = {'s': 'You avoid {N}\'s attack', 't': '{n} avoids your attack', 'e': '{n} avoids {N}\'s attack'}

    def invoke(self, source, **ignored):
        pass

    def apply(self, owner, attack):
        try:
            self._validate_weapon(owner.weapon_type)
            self._validate_delivery(attack)
        except ActionError:
            return
        attack.adj_accuracy -= attr_calc(owner, accuracy_calc)
        if attack.adj_accuracy < 0:
            return
        attack.adj_damage -= attr_calc(owner, absorb_calc)

    def _validate_delivery(self, attack):
        if self.delivery == 'any':
            return
        if self.delivery != attack.delivery:
            raise ActionError("You need a different weapon for that")