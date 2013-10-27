from lampost.env.room import Exit

exit_cost_map = {}


def find_cost(room):
    try:
        return exit_cost_map[room.size]
    except KeyError:
        exit_cost_map[room.size] = {'action': room.size, 'stamina' : room.size / 2}
        return skill_cost


class ExitLP(Exit):
    prep_time = 1

    def prepare_action(self, source, **ignored):
        source.display_line("You head {}.".format(self.direction.desc))

    def __call__(self, source, **ignored):
        find_cost(self.room).apply(source)
        super(ExitLP, self).__call__(source)
