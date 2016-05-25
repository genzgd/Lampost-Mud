from lampmud.comm.broadcast import BroadcastMap
from lampmud.context.config import m_configured
from lampmud.context.resource import m_requires, requires
from lampmud.datastore.dbofield import DBOField, DBOLField
from lampmud.env.movement import Direction
from lampmud.env.room import Room
from lampmud.gameops import target_gen
from lampmud.gameops.action import convert_verbs, ActionError
from lampmud.model.item import ItemDBO

m_requires(__name__, 'log', 'datastore', 'dispatcher')

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

    def get_room(self, room):
        if not room:
            error("Null room passed to area instance")
            return
        try:
            instance = self.rooms[room.dbo_id]
        except KeyError:
            instance = room.clone()
            instance.instance = self
            self.rooms[room.dbo_id] = instance
        return instance


verb_exit = BroadcastMap(ea='{n} leaves {N}')
dir_exit = BroadcastMap(ea='{n} leaves to the {N}')
verb_entry = BroadcastMap(ea='{n} arrives {N}')
dir_enter = BroadcastMap(ea='{n} arrives from the {N}')


@requires('instance_manager')
class Entrance(ItemDBO):
    class_id = 'entrance'

    verb = DBOField('enter')
    direction = DBOField(None)
    destination = DBOField(dbo_class_id="room", required=True)
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
            source.display_line('Exit: {0}  {1}'.format(self._dir.desc, self.destination.title), 'exit')
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
            destination = self.destination
        source.change_env(destination, self)
