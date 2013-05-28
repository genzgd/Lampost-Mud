from lampost.gameops.action import action_handler
from lampost.lpflavor.attributes import need_refresh
from lampost.model.entity import Entity


class EntityLP(Entity):
    dbo_fields = Entity.dbo_fields

    weapon = None
    current_target = None

    _refresh_pulse = None
    _current_action = None
    _current_args = None
    _next_command = None
    _action_pulse = None
    effects = []
    skills = {}
    avoid_skills = []
    absorb_skills = []

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
            self._current_action = action
            self._current_args = act_args
            self._action_pulse = self.register_p(self._finish_action, pulses=prep_time, priority=priority)
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
        self.unregister(self._action_pulse)
        target = self._current_args['target']
        if target and not target in self.target_map:
            raise ActionError("{} is no longer here.", target.name)
        super(EntityLP, self).process_action(self._current_action, self._current_args)
        del self._current_action
        del self._current_args
        del self._action_pulse
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
        adj_accuracy, miss_msg = self.check_avoid(attack.damage_type, attack.accuracy)
        if adj_accuracy <= 0:
            source.broadcast(target=self, **(miss_msg if miss_msg else attack.fail_map))
            return
        adj_damage, absorb_msg = self.check_absorb(attack.damage_type, attack.damage)
        if adj_damage <= 0:
            source.broadcast(target=self, **(miss_msg if miss_msg else attack.fail_map))
            return
        source.broadcast(target=self, **attack.success_map)
        current_pool = getattr(self, attack.damage_pool)
        setattr(self, attack.damage_pool, current_pool - adj_damage)
        self.check_status()

    def check_avoid(self, damage_type, accuracy):
        for skill in self.avoid_skills:
            if skill.damage_type != damage_type and skill.damage_type != 'any':
                continue


    def check_absorb(self, damage_type, damage):
        return damage, None

    def check_status(self):
        if self.health < 0:
            self.die()



