from lampost.datastore.dbofield import DBOField
import lampost.env.room
from lampost.gameops.action import ActionError
from lampost.context.config import m_configured

m_configured(__name__, 'room_stamina', 'room_action', 'default_room_size')

exit_cost_map = {}
prep_multiplier = 1


def find_cost(room):
    if room and room.size:
        try:
            return exit_cost_map[room.size]
        except KeyError:
            exit_cost_map[room.size] = {'action': int(room_stamina * room.size / default_room_size),
                                        'stamina': int(room_action * room.size / default_room_size)}
            return exit_cost_map[room.size]


class ExitLP(lampost.env.room.Exit):
    class_id = 'exit'

    guarded = DBOField(False)
    door_key = DBOField()

    @property
    def prep_time(self):
        return prep_multiplier * self.dbo_owner.size // 10

    def prepare_action(self, source, **_):
        if self.guarded:
            guards = [guard for guard in source.env.denizens if guard.affinity != source.affinity]
            if guards:
                raise ActionError(guards[0].guard_msg.format(source=guards[0].name, exit=self._dir.desc))
        source.display_line("You head {}.".format(self._dir.desc))

    def _move_user(self, source):
        source.apply_costs(find_cost(self.dbo_owner))
        super()._move_user(source)
