from lampost.db.dbofield import DBOField, DBOLField

from lampost.di.resource import Injected, module_inject
from lampost.gameops import target
from lampost.gameops.action import ActionError

from lampmud.comm.broadcast import BroadcastMap
from lampmud.env.movement import Direction
from lampmud.model.item import ItemDBO

log = Injected('log')
ev = Injected('dispatcher')
instance_manager = Injected('instance_manager')
module_inject(__name__)


class AreaInstance():
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.entities = set()
        self.rooms = {}
        self.pulse_stamp = ev.current_pulse

    def add_entity(self, entity):
        self.entities.add(entity)
        entity.instance = self
        self.pulse_stamp = ev.current_pulse

    def remove_entity(self, entity):
        if entity in self.entities:
            del entity.instance
            self.entities.remove(entity)
            if not self.entities:
                self.clear_rooms()
                if entity.group:
                    entity.group.instance = None
                instance_manager.delete(self.instance_id)

    def clear_rooms(self):
        for room in self.rooms.values():
            room.detach()

    def get_room(self, room):
        if not room:
            log.error("Null room passed to area instance")
            return
        try:
            my_room = self.rooms[room.dbo_id]
        except KeyError:
            my_room = room.clone()
            my_room.instance = self
            self.rooms[room.dbo_id] = my_room
        return my_room


verb_exit = BroadcastMap(ea='{n} leaves {N}')
dir_exit = BroadcastMap(ea='{n} leaves to the {N}')
verb_entry = BroadcastMap(ea='{n} arrives {N}')
dir_enter = BroadcastMap(ea='{n} arrives from the {N}')


class Entrance(ItemDBO):
    class_id = 'entrance'

    destination = DBOLField(dbo_class_id="room", required=True)
    verb = DBOField('enter')
    direction = DBOField(None)
    instanced = DBOField(True)
    edit_required = DBOField(True)

    match_args = 'source',

    def _on_hydrated(self):
        if self.direction:
            self._dir = Direction.ref_map[self.direction]
            self.verbs = self._dir.obj_id, self._dir.desc
            self.target_class = 'no_args'
        else:
            self._dir = None
            self.verbs = self.verb
            self.target_class = target.make_gen('action')
        if not self.title and self.verb:
            self.title = self.verb

    @property
    def from_name(self):
        return Direction.ref_map.get(self._dir.rev_key).desc if self.direction else self.title

    @property
    def entry_msg(self):
        return verb_entry if self.verb else verb_entry

    @property
    def exit_msg(self):
        return verb_exit if self.verb else dir_exit

    def glance(self, source):
        if self._dir:
            source.display_line('Exit: {0}  {1}'.format(self._dir.desc, self.destination.title), 'exit')
        else:
            source.display_line(self.title, 'exit')

    def __call__(self, source):
        if self.instanced:
            if getattr(source, 'group', None):
                if source.group.instance:
                    instance = source.group.instance
                    if self.destination not in instance.rooms:
                        raise ActionError("Your group has entered a different instance.  You must leave your group to go this way.")
                else:
                    instance = source.group.instance = instance_manager.next_instance()
            else:
                instance = instance_manager.next_instance()
            destination = instance.get_room(self.destination)
        else:
            destination = self.destination
        source.change_env(destination, self)
