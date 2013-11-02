from lampost.context.resource import m_requires
from lampost.gameops.action import action_handler
from lampost.lpflavor.attributes import need_refresh, POOL_LIST
from lampost.model.entity import Entity
from lampost.util.lmutil import args_print

m_requires('log', 'tools', __name__)


class EntityLP(Entity):
    health = 0
    stamina = 0
    mental = 0
    action = 0

    weapon = None
    current_target = None

    _refresh_pulse = None
    _current_action = None
    _next_command = None
    _action_pulse = None
    effects = []
    skills = {}

    @property
    def weapon_type(self):
        if self.weapon:
            return self.weapon_type

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
            self._current_action = action, act_args, self.register_p(self._finish_action, pulses=prep_time, priority=priority)
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
        self.unregister(action_pulse)
        target = action_args.get('target', None)
        if target and not target in self.target_map:
            raise ActionError("{} is no longer here.", target.name)
        super(EntityLP, self).process_action(action, action_args)
        if self._next_command:
            self.parse(self._next_command)
            del self._next_command

    def start_refresh(self):
        if not self._refresh_pulse and need_refresh(self):
            self._refresh_pulse = self.register_p(self._refresh, pulses=4)

    def _refresh(self):
        if need_refresh(self):
            self.action += min(40, self.base_action - self.action)
            self.stamina += min(1, self.base_stamina - self.stamina)
            self.health += min(1, self.base_health - self.health)
        else:
            self.unregister(self._refresh_pulse)
            del self._refresh_pulse

    def rec_attack(self, source, attack):
        for defense in self.defenses:
            defense.apply(self, attack)
            if attack.adj_damage < 0 or attack.adj_accuracy < 0:
                if defense.success_map:
                    self.broadcast(target=source, **defense.success_map)
                else:
                    source.broadcast(target=self, **attack.fail_map)
                return
        source.broadcast(target=self, **attack.success_map)
        current_pool = getattr(self, attack.damage_pool)
        setattr(self, attack.damage_pool, current_pool - attack.adj_damage)
        combat_log(source, self.rec_status, self)
        combat_log(self, self.rec_status, self)
        self.check_status()

    def apply_costs(self, costs):
        for pool, cost in costs.iteritems():
            if getattr(self, pool, 0) < cost:
                entity.start_refresh()
                raise ActionError("Your condition prevents you from doing that.")
        for pool, cost in costs.iteritems():
            setattr(self, pool, getattr(self, pool) - cost)
        self.start_refresh()

    def check_status(self):
        if self.health <= 0:
            self.die()
        else:
            self.start_refresh()

    def rec_status(self):
        return ''.join(['{N} STATUS--', ''.join(["{0}: {1} ".format(pool_name, getattr(self, pool_name))
            for pool_name in POOL_LIST])])
