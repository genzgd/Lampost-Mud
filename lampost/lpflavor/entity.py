from lampost.context.resource import m_requires
from lampost.gameops.action import action_handler, ActionError
from lampost.lpflavor.ai import Fight
from lampost.lpflavor.attributes import need_refresh, POOL_LIST
from lampost.lpflavor.combat import calc_consider
from lampost.model.entity import Entity

m_requires('log', 'tools', 'dispatcher', __name__)


def _post_init():
    register('game_settings', update_settings)


def update_settings(game_settings):
    EntityLP._refresh_interval = game_settings.get('refresh_interval', 12)
    EntityLP._refresher['stamina'] = game_settings.get('stamina_refresh', 8)
    EntityLP._refresher['health'] = game_settings.get('health_refresh', 1)
    EntityLP._refresher['mental'] = game_settings.get('mental_refresh', 1)
    EntityLP._refresher['action'] = game_settings.get('action_refresh', 40)


class EntityLP(Entity):
    health = 0
    stamina = 0
    mental = 0
    action = 0
    auto_fight = True

    weapon = None
    last_opponent = None

    _refresh_pulse = None
    _current_action = None
    _next_command = None
    _action_pulse = None
    _refresher = {}

    def __init__(self, dbo_id=None):
        super(EntityLP, self).__init__(dbo_id)
        self.effects = set()
        self.defenses = set()
        self.fight = Fight(self)
        self.equip_slots = {}

    def baptise(self):
        super(EntityLP, self).baptise()
        for article in self.inven:
            if article.current_slot:
                self._do_equip(article, article.current_slot)

    @property
    def weapon_type(self):
        if self.weapon:
            return self.weapon.weapon_type

    def filter_actions(self, matches):
        if not self._current_action:
            return matches
        return [(action, verb, args) for action, verb, args in matches if not hasattr(action, 'prep_time')]

    @action_handler
    def start_action(self, action, act_args):
        if hasattr(action, 'prepare_action'):
            action.prepare_action(**act_args)
        priority = -len(self.followers)
        prep_time = getattr(action, 'prep_time', None)
        if prep_time:
            self._current_action = action, act_args, register_p(self._finish_action, pulses=prep_time, priority=priority, repeat=False)
        else:
            super(EntityLP, self).process_action(action, act_args)
        self.check_follow(action, act_args)

    def handle_parse_error(self, error, command):
        if self._current_action:
            if self._next_command:
                self.display_line("You can only do so much at once!")
            else:
                self._next_command = command
        else:
            super(EntityLP, self).handle_parse_error(error, command)

    @action_handler
    def _finish_action(self):
        action, action_args, action_pulse = self._current_action
        del self._current_action
        target = action_args.get('target', None)
        if target and not target in self.target_map:
            raise ActionError("{} is no longer here.", target.name)
        super(EntityLP, self).process_action(action, action_args)
        if self._next_command:
            self.parse(self._next_command)
            del self._next_command
        elif self.auto_fight:
            self.check_fight()

    def start_refresh(self):
        if not self._refresh_pulse and need_refresh(self):
            self._refresh_pulse = register_p(self._refresh, pulses=self._refresh_interval)

    def _refresh(self):
        if self.status == 'dead' or not need_refresh(self):
            unregister(self._refresh_pulse)
            del self._refresh_pulse
            return
        for pool_id, base_pool_id in POOL_LIST:
            new_value = getattr(self, pool_id) + self._refresher[pool_id]
            setattr(self, pool_id, min(new_value, getattr(self, base_pool_id)))
        self.status_change()
        self.check_fight()

    def rec_attack(self, source, attack):
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
        self.check_status()

    def start_combat(self, source):
        self.last_opponent = source
        if source not in self.fight.opponents.viewkeys():
            self.fight.add(source)
            self.check_fight()

    def check_fight(self):
        if not self._current_action and self.auto_fight:
            self.fight.select_action()

    def end_combat(self, source):
        self.fight.remove(source)
        if self.last_opponent == source:
            del self.last_opponent
        self.status_change()

    def check_costs(self, costs):
        for pool, cost in costs.iteritems():
            if getattr(self, pool, 0) < cost:
                raise ActionError("Your condition prevents you from doing that.")

    def apply_costs(self, costs):
        self.check_costs(costs)
        for pool, cost in costs.iteritems():
            setattr(self, pool, getattr(self, pool) - cost)
        self.check_status()

    def equip_article(self, article):
        if not article in self.inven:
            raise ActionError('You must pick up the item before you can equip it.')
        if article.current_slot:
            raise ActionError('This article is already equipped.')
        if article.equip_slot == 'none':
            raise ActionError('This is not something you can equip.')
        if article.art_type == 'weapon' and self.weapon:
            self.remove_article(self.weapon)
        equip_slot = self._find_slot(article.equip_slot)
        if self._slot_filled(equip_slot):
            self._remove_by_slot(equip_slot)
            if self._slot_filled(equip_slot):
                raise ActionError('You have no place to put that.')
        self._do_equip(article, equip_slot)

    def remove_article(self, article):
        if not article.equip_slot:
            raise ActionError("{0} is not equipped.".format(article.name))
        if not article in self.inven:
            raise ActionError("{0} is not yours.".format(article.name))
        if article.equip_slot == 'two_hand':
            del self.equip_slots['r_hand']
            del self.equip_slots['l_hand']
        else:
            del self.equip_slots[article.current_slot]
        article.current_slot = None
        if article.art_type == 'weapon':
            self.weapon = None
        article.on_removed(self)

    def rec_consider(self, **ignored):
        return calc_consider(self)

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
        if self.health <= 0:
            self._cancel_actions()
            self.fight.lose()
            self.die()
        else:
            self.start_refresh()
        self.status_change()
        try:
            self.last_opponent.status_change()
        except AttributeError:
            pass

    def _cancel_actions(self):
        if self._current_action:
            unregister(self._current_action[2])
            del self._current_action
        if self._next_command:
            del self._next_command

    def die(self):
        self.status = 'dead'
        super(EntityLP, self).die()

    def status_change(self):
        pass

    def detach(self):
        self._cancel_actions()
        if self._refresh_pulse:
            del self._refresh_pulse
        super(EntityLP, self).detach()

    @property
    def display_status(self):
        display_status = super(EntityLP, self).display_status
        for pool_id, base_pool_id in POOL_LIST:
            display_status[pool_id] = getattr(self, pool_id)
            display_status[base_pool_id] = getattr(self, base_pool_id)
        return display_status

    def rec_status(self):
        return ''.join(['{N} STATUS--', ''.join(["{0}: {1} ".format(pool_id, getattr(self, pool_id))
                                                 for pool_id, ignored in POOL_LIST])])
