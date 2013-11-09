from lampost.env.room import Exit, Room

exit_cost_map = {}


def find_cost(room):
    try:
        return exit_cost_map[room.size]
    except KeyError:
        exit_cost_map[room.size] = {'action': action_calc * room.size / Room.size,
                                    'stamina': stamina_calc * room.size / Room.size}
        return exit_cost_map[room.size]


class ExitLP(Exit):
    prep_time = 1

    def prepare_action(self, source, **ignored):
        source.display_line("You head {}.".format(self.direction.desc))

    def __call__(self, source, **ignored):
        source.apply_costs(find_cost(self.room))
        super(ExitLP, self).__call__(source)
