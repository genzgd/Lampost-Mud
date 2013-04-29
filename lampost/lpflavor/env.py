from lampost.env.room import Exit


class ExitLP(Exit):
    cost = [{'pool': 'action', 'cost': 20}]
    duration = 1
    followable = True

    def prepare_action(self, source):
        source.display_line("You head {}.".format(self.direction.desc))
