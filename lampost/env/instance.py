from lampost.comm.broadcast import BroadcastMap
from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.gameops import target_gen
from lampost.gameops.action import convert_verbs, ActionError
from lampost.gameops.display import EXIT_DISPLAY

m_requires(__name__, 'datastore')

instance_id = 0


def next_instance():
    global instance_id
    instance_id += 1
    return AreaInstance(instance_id)


class AreaInstance():
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.entities = set()
        self.rooms = {}

    def add_entity(self, entity):
        self.entities.add(entity)
        entity.instance = self

    def remove_entity(self, entity):
        if entity in self.entities:
            del entity.instance
            self.entities.remove(entity)
            if not self.entities:
                self.clear_rooms()
                if entity.group:
                    entity.group.instance = None

    def clear_rooms(self):
        for room in self.rooms.values():
            room.clean_up()

    def get_room(self, room_id):
        try:
            room = self.rooms[room_id]
        except KeyError:
            room = load_object(room_id, Room).clone()
            room.instance = self
            self.rooms[room_id] = room
        return room


verb_exit = BroadcastMap(ea='{n} leaves {N}')
dir_exit = BroadcastMap(ea='{n} leaves to the {N}')
verb_entry = BroadcastMap(ea='{n} arrives {N}')
dir_enter = BroadcastMap(ea='{n} arrives from the {N}')


class Entrance(RootDBO):
    class_id = 'entrance'

    verb = DBOField('enter')
    direction = DBOField(None)
    destination = DBOField()
    instanced = DBOField(True)
    edit_required = DBOField(True)

    msg_class = "__call__"

    def on_loaded(self):
        if self.direction:
            self._dir = Direction.ref_map[self.direction]
            self.verbs = (self._dir.obj_id,), (self._dir.desc,)
            self.target_class = 'no_args'
        else:
            self.verbs = convert_verbs(self.verb)
            self.target_class = [target_gen.action]
        if not self.title and self.verb:
            self.title = self.verb

    @property
    def dest_room(self):
        return load_object(self.destination, Room)

    @property
    def name(self):
        return self.verb or self._dir.desc

    @property
    def from_name(self):
        return self.verb if self.verb else Direction.ref_map.get(self._dir.rev_key).desc

    @property
    def entry_msg(self):
        return verb_entry if self.verb else verb_entry

    @property
    def exit_msg(self):
        return verb_exit if self.verb else dir_exit

    def glance(self, source, **_):
        if self._dir:
            source.display_line('Exit: {0}  {1}'.format(self._dir.desc, self.dest_room.title), EXIT_DISPLAY)
        else:
            source.display_line(self.title, EXIT_DISPLAY)

    def __call__(self, source, **_):
        if self.instanced:
            if source.group:
                if source.group.instance:
                    instance = source.group.instance
                    if self.destination not in instance.rooms:
                        raise ActionError("Your group has entered a different instance.  You must leave your group to go this way.")
                else:
                    instance = source.group.instance = next_instance()
            else:
                instance = next_instance()
            destination = instance.get_room(self.destination)
        else:
            destination = self.dest_room
        source.change_env(destination, self)
