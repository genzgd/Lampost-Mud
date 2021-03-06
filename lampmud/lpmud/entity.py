from lampost.db.dbo import DBOAspect
from lampost.db.dbofield import DBOField
from lampost.di.app import on_app_start
from lampost.di.config import on_config_change, config_value
from lampost.di.resource import Injected, module_inject
from lampost.gameops.action import action_handler, ActionError
from lampost.meta.auto import AutoField

from lampmud.lpmud import attributes
from lampmud.lpmud.combat.core import calc_consider
from lampmud.lpmud.combat.fight import Fight
from lampmud.model.entity import Entity
from lampmud.mud.tools import combat_log

log = Injected('log')
ev = Injected('dispatcher')
acs = Injected('action_system')
module_inject(__name__)


@on_app_start
@on_config_change
def _config():
    global refresh_interval
    global refresh_rates
    refresh_interval = config_value('refresh_interval')
    refresh_rates = config_value('refresh_rates')


class EntityLP(Entity):
    health = 0
    stamina = 0
    mental = 0
    action = 0
    auto_fight = True

    weapon = None
    last_opponent = None

    _refreshing = AutoField(False)

    _current_action = AutoField()
    _next_command = AutoField()
    _action_target = AutoField()

    def _on_attach(self):
        self.effects = set()
        self.defenses = set()
        self.equip_slots = {}
        for article in self.inven:
            if getattr(article, 'current_slot', None):
                self._do_equip(article, article.current_slot)
        self.fight.update_skills()

    def _on_detach(self):
        self._cancel_actions()
        del self.effects
        del self.defenses
        del self.equip_slots

    def check_costs(self, costs):
        for pool, cost in costs.items():
            if getattr(self, pool, 0) < cost:
                raise ActionError("Your condition prevents you from doing that.")

    def apply_costs(self, costs):
        self.check_costs(costs)
        for pool, cost in costs.items():
            setattr(self, pool, getattr(self, pool) - cost)

    def filter_actions(self, matches):
        if not self._current_action:
            return matches
        return [match for match in matches if not getattr(match.action, 'prep_time', None)]

    @action_handler
    def start_action(self, action, act_args):
        self._current_action = action, act_args
        if hasattr(action, 'prepare_action'):
            try:
                if self.dead:
                    raise ActionError("Ah, would that you could.  Was it so long ago that you had such freedom of movement?")
                action.prepare_action(**act_args)
            except ActionError as act_err:
                self._current_action = None
                raise act_err
        priority = -len(self.followers)
        prep_time = getattr(action, 'prep_time', None)
        self._action_target = act_args.get('target', None)
        acs.add_action(self, self._current_action, prep_time, self.finish_action, priority)
        self.check_follow(action, act_args)

    def handle_parse_error(self, error, command):
        if self._current_action:
            if self._next_command:
                self.display_line("You can only do so much at once!")
            else:
                self._next_command = command
        else:
            super().handle_parse_error(error, command)

    @action_handler
    def finish_action(self, system_action, affected):
        if system_action != self._current_action:
            if self._current_action:
                log.warn("Action mismatch")
            return
        action, action_args = self._current_action
        affected.add(self._action_target)
        self._current_action = self._action_target = None
        super().process_action(action, action_args)
        if self._next_command:
            self.parse(self._next_command)
            self._next_command = None

    def resolve_actions(self):
        self.check_status()
        self.check_fight()

    def entity_leave_env(self, entity, exit_action):
        super().entity_leave_env(entity, exit_action)
        if self._current_action and self._action_target == entity:
            self._cancel_actions()

    def _refresh(self, *_):
        for pool_id, base_pool_id in attributes.pool_keys:
            new_value = getattr(self, pool_id) + refresh_rates[pool_id]
            setattr(self, pool_id, min(new_value, getattr(self, base_pool_id)))
        self._refreshing = False

    @property
    def weapon_type(self):
        if self.weapon:
            return self.weapon.weapon_type

    def attacked(self, source, attack):
        for defense in self.defenses:
            defense.apply(self, attack)
            if attack.adj_damage <= 0 or attack.adj_accuracy <= 0:
                if defense.success_map:
                    self.broadcast(target=source, **defense.success_map)
                else:
                    source.broadcast(verb=attack.verb, target=self, **attack.fail_map)
                return
        source.broadcast(verb=attack.verb, target=self, **attack.success_map)
        current_pool = getattr(self, attack.damage_pool)
        setattr(self, attack.damage_pool, current_pool - attack.adj_damage)
        combat_log(source,
                   lambda: ''.join(['{N} result -- ', attack.damage_pool, ' old: ',
                                    str(current_pool), ' new: ', str(current_pool - attack.adj_damage)]),
                   self)

    def start_combat(self, source):
        self.last_opponent = source
        self.fight.add(source)

    def check_fight(self):
        if self.auto_fight and not self._current_action and not self._next_command:
            self.fight.select_action()

    def end_combat(self, source, victory):
        self.fight.end(source, victory)
        if self.last_opponent == source:
            del self.last_opponent
        self.status_change()

    def equip_article(self, article):
        if article.art_type == 'weapon' and self.weapon:
            self.remove_article(self.weapon)
        equip_slot = self._find_slot(article.equip_slot)
        if self._slot_filled(equip_slot):
            self._remove_by_slot(equip_slot)
            if self._slot_filled(equip_slot):
                raise ActionError('You have no place to put that.')
        self._do_equip(article, equip_slot)

    def remove_article(self, article):
        if article.equip_slot == 'two_hand':
            del self.equip_slots['r_hand']
            del self.equip_slots['l_hand']
        else:
            del self.equip_slots[article.current_slot]
        article.current_slot = None
        if article.art_type == 'weapon':
            self.weapon = None
        article.on_removed(self)

    def considered(self, **_):
        return calc_consider(self)

    def check_drop(self, article, quantity=None):
        if getattr(article, 'current_slot', None):
            raise ActionError("You must unequip the item before dropping it.")

    def _do_equip(self, article, equip_slot):
        self.equip_slots[equip_slot] = article
        article.current_slot = equip_slot
        article.on_equipped(self)
        if article.art_type == 'weapon':
            self.weapon = article

    def _find_slot(self, equip_slot):
        if equip_slot == 'finger':
            if self._slot_filled('r_finger'):
                return 'r_finger'
            return 'l_finger'
        elif equip_slot == 'wrist':
            if self._slot_filled('r_wrist'):
                return 'r_wrist'
            return 'l_wrist'
        elif equip_slot == 'one-hand':
            if self._find_slot('r_hand'):
                return 'r_hand'
            return 'l_hand'
        return equip_slot

    def _slot_filled(self, equip_slot):
        if equip_slot == 'two-hand':
            if self.equip_slots.get('r_hand') or self.equip_slots.get('l_hand'):
                return None
        return self.equip_slots.get(equip_slot)

    def _remove_by_slot(self, equip_slot):
        if equip_slot == 'two_hand':
            self._remove_by_slot('r_hand')
            self._remove_by_slot('l_hand')
            return
        article = self.equip_slots.get(equip_slot)
        if article:
            self.remove_article(article)

    def check_status(self):
        if self.status == 'dead':
            pass
        elif self.health <= 0:
            self._cancel_actions()
            self.fight.end_all()
            self.die()
        elif not self._refreshing and attributes.need_refresh(self):
            acs.add_action(self, None, refresh_interval, self._refresh, -1000)
            self._refreshing = True
        self.status_change()

    def _cancel_actions(self):
        if self._current_action:
            del self._current_action
            try:
                del self._action_target
            except AttributeError:
                pass
        if self._next_command:
            del self._next_command

    def die(self):
        self._death_effects()
        super().die()

    def _death_effects(self):
        self.status = 'dead'
        self.action = 0
        self.health = 0
        self.stamina = 0
        self.mental = 0

    def status_change(self):
        self.pulse_stamp = ev.current_pulse

    @property
    def display_status(self):
        display_status = super().display_status
        for pool_id, base_pool_id in attributes.pool_keys:
            display_status[pool_id] = getattr(self, pool_id)
            display_status[base_pool_id] = getattr(self, base_pool_id)
        return display_status

    def combat_status(self):
        return ''.join(['{N} STATUS--', ''.join(["{0}: {1} ".format(pool_id, getattr(self, pool_id))
                                                 for pool_id, _ in attributes.pool_keys])])


class Skilled(DBOAspect):
    skills = DBOField({}, 'untyped')

    def _on_attach(self):
        self.fight = Fight(self)

    def add_skill(self, skill):
        if skill.template_key in self.skills:
            raise ActionError("Skill already exists.")
        self.skills[skill.template_key] = skill
        self._apply_skill(skill)

    def _apply_skill(self, skill):
        if skill.auto_start:
            skill.invoke(self)
        else:
            self.enhance_soul(skill)
        try:
            self.fight.update_skills()
        except AttributeError:
            pass

    def remove_skill(self, skill_id):
        try:
            skill = self.skills.pop(skill_id)
            if skill.auto_start:
                skill.revoke(self)
            else:
                 self.diminish_soul(skill)
            self.fight.update_skills()
        except KeyError:
            raise ActionError('{} does not have that skill'.format(self.name))


