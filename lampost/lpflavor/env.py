from lampost.env.room import Exit
from lampost.lpflavor.skill import SkillCost


exit_cost_map = {}


def find_cost(room):
    try:
        return exit_cost_map[room.size]
    except KeyError:
        skill_cost = SkillCost('action', room.size).add('stamina', room.size / 2)
        exit_cost_map[room.size] = skill_cost
        return skill_cost


class ExitLP(Exit):
    prep_time = 1

    def prepare_action(self, source, **ignored):
        source.display_line("You head {}.".format(self.direction.desc))

    def __call__(self, source, **ignored):
        find_cost(self.room).apply(source)
        super(ExitLP, self).__call__(source)
