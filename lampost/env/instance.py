from lampost.comm.broadcast import BroadcastMap
from lampost.context.config import m_configured
from lampost.context.resource import m_requires, requires
from lampost.datastore.dbofield import DBOField
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.gameops import target_gen
from lampost.gameops.action import convert_verbs, ActionError
from lampost.model.item import BaseItem

m_requires(__name__, 'datastore', 'dispatcher')

m_configured(__name__, 'instance_preserve_hours')

instance_map = {}


class InstanceManager():
    def _post_init(self):
        register('maintenance', self.remove_old)

    def next_instance(self):
        instance_id = db_counter('instance_id')
        area_instance = AreaInstance(instance_id)
        instance_map[instance_id] = area_instance
        return area_instance

    def remove_old(self):
        stale_pulse = future_pulse(instance_preserve_hours * 60 * 60)
        for instance_id, instance in instance_map.copy().items():
            if instance.pulse_stamp < stale_pulse and not [entity for entity in instance.entities
                                                           if hasattr(entity, 'is_player') and entity.session]:
                del instance_map[instance_id]

    def get(self, instance_id):
        return instance_map.get(instance_id)


class AreaInstance():
    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.entities = set()
        self.rooms = {}
        self.pulse_stamp = current_pulse()

    def add_entity(self, entity):
        self.entities.add(entity)
        entity.instance = self
        self.pulse_stamp = current_pulse()

    def remove_entity(self, entity):
        if entity in self.entities:
            del entity.instance
            self.entities.remove(entity)
            if not self.entities:
                self.clear_rooms()
                if entity.group:
                    entity.group.instance = None
            del instance_map[self.instance_id]

    def clear_rooms(self):
        for room in self.rooms.values():
            room.clean_up()

    def get_room(self, room_id):
        try:
            room = self.rooms[room_id]
        except KeyError:
            room = load_object(room_id, Room)
            if not room:
                return
            room = room.clone()
            room.instance = self
            self.rooms[room_id] = room
        return room


verb_exit = BroadcastMap(ea='{n} leaves {N}')
dir_exit = BroadcastMap(ea='{n} leaves to the {N}')
verb_entry = BroadcastMap(ea='{n} arrives {N}')
dir_enter = BroadcastMap(ea='{n} arrives from the {N}')


@requires('instance_manager')
class Entrance(BaseItem):
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
            self._dir = None
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
            source.display_line('Exit: {0}  {1}'.format(self._dir.desc, self.dest_room.title), 'exit')
        else:
            source.display_line(self.title, 'exit')

    def __call__(self, source, **_):
        if self.instanced:
            if source.group:
                if source.group.instance:
                    instance = source.group.instance
                    if self.destination not in instance.rooms:
                        raise ActionError("Your group has entered a different instance.  You must leave your group to go this way.")
                else:
                    instance = source.group.instance = self.instance_manager.next_instance()
            else:
                instance = self.instance_manager.next_instance()
            destination = instance.get_room(self.destination)
        else:
            destination = self.dest_room
        source.change_env(destination, self)
