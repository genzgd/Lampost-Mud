from lampost.datastore.dbo import DBOField
import lampost.env.room
from lampost.gameops.action import ActionError

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

    guarded = DBOField(False)
    door_key = DBOField()

    def prepare_action(self, source, **_):
        if self.guarded:
            guards = [guard for guard in source.env.denizens if guard.affinity != source.affinity]
            if guards:
                raise ActionError(guards[0].guard_msg.format(source=guards[0].name, exit=self._dir.desc))
        source.display_line("You head {}.".format(self._dir.desc))

    def _move_user(self, source):
        source.apply_costs(find_cost(source.env))
        super()._move_user(source)
