import lampost.env.room

exit_cost_map = {}


def find_cost(room):
    if room and room.size:
        try:
            return exit_cost_map[room.size]
        except KeyError:
            exit_cost_map[room.size] = {'action': int(action_calc * room.size / lampost.env.room.default_room_size),
                                        'stamina': int(stamina_calc * room.size / lampost.env.room.default_room_size)}
            return exit_cost_map[room.size]


class ExitLP(lampost.env.room.Exit):
    class_id = 'exit'
    prep_time = 1

    def prepare_action(self, source, **ignored):
        source.display_line("You head {}.".format(self.direction.desc))

    def __call__(self, source, **ignored):
        source.apply_costs(find_cost(source.env))
        super(ExitLP, self).__call__(source)
