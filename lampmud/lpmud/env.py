from lampost.db.dbofield import DBOField
from lampost.di.app import on_app_start
from lampost.gameops.action import ActionError
from lampost.di.config import on_config_change, config_value

from lampmud.env.room import Exit

exit_cost_map = {}
prep_multiplier = 1


@on_app_start
@on_config_change
def _config():
    global room_stamina
    global room_action
    global default_room_size
    room_stamina = config_value('room_stamina')
    room_action = config_value('room_action')
    default_room_size = config_value('default_room_size')


def find_cost(room):
    if room and room.size:
        try:
            return exit_cost_map[room.size]
        except KeyError:
            exit_cost_map[room.size] = {'action': int(room_stamina * room.size / default_room_size),
                                        'stamina': int(room_action * room.size / default_room_size)}
            return exit_cost_map[room.size]


class ExitLP(Exit):
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
        source.env.allow_leave(source, self)

    def _move_user(self, source):
        source.apply_costs(find_cost(self.dbo_owner))
        super()._move_user(source)
