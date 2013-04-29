from lampost.model.entity import Entity


class EntityLP(Entity):
    dbo_fields = Entity.dbo_fields + ("effects", "skills")

    def baptise(self, soul):
        super(EntityLP, self).baptise(soul)
        self._current_action = None
        self._next_command = None
        self._action_pulse = None
        self.register_p(self._refresh, pulses=4)

    def filter_actions(self, matches):
        if not self._current_action:
            return matches
        return [(action, verb, args) for action, verb, args in matches if not hasattr(action, 'duration')]

    def process_action(self, action, act_args):
        try:
            action.prepare_action(self)
        except AttributeError:
            pass
        priority = -len(self.followers)
        duration = getattr(action, 'duration', None)
        if duration:
            self._current_action = action, act_args
            self._action_pulse = self.register_p(self._finish_action, pulses=duration, priority=priority)
        else:
            self._do_action(action, act_args)
        if hasattr(action, 'followable'):
            for follower in self.followers:
                follow_args = act_args.copy()
                follow_args['source'] = follower
                follower.process_action(action, follow_args)

    def handle_parse_error(self, error, command):
        if self._current_action:
            if self._next_command:
                self.display_line("You can only do so much at once!")
            else:
                self._next_command = command
        else:
            super(EntityLP, self).handle_parse_error(error, command)

    def _do_action(self, action, act_args):
        if getattr(action, 'cost', None):
            for pool_cost in action.cost:
                if pool_cost['cost'] > getattr(self, pool_cost['pool']):
                    self.display_line("Your condition prevents you from doing that.")
                    return
            for pool_cost in action.cost:
                setattr(self, pool_cost['pool'], getattr(self, pool_cost['pool']) - pool_cost['cost'])
        action(**act_args)

    def _finish_action(self):
        self._do_action(*self._current_action)
        self.unregister(self._action_pulse)
        self._current_action = None
        self._action_pulse = None
        if self._next_command:
            self.parse(self._next_command)
            self._next_command = None

    def _refresh(self):
        self.action += 40











