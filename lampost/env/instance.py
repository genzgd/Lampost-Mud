from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import convert_verbs, item_action
from lampost.gameops.display import EXIT_DISPLAY
from lampost.gameops.script import Script
from lampost.gameops.target import TargetClass

m_requires('datastore', __name__)

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

    def clear_rooms(self):
        for room in self.rooms.values():
            room.clean_up()

    def get_room(self, room_id):
        try:
            room = self.rooms[room_id]
        except KeyError:
            room = load_by_key('room', room_id).clone()
            room.instance = self
            self.rooms[room_id] = room
        return room


class Entrance(Feature):
    sub_class_id = 'entrance'

    verb = DBOField('enter')
    direction = DBOField(None, 'direction')
    destination = DBOField()
    instanced = DBOField(True)
    edit_required = DBOField(True)

    msg_class = "__call__"

    def on_loaded(self):
        if self.direction:
            self.verbs = (self.direction.obj_id,), (self.direction.desc,)
            self.target_class = [TargetClass.NO_ARGS]
        else:
            self.verbs = convert_verbs(self.verb)
            self.target_class = [TargetClass.ACTION]
        if not self.title and self.verb:
            self.title = self.verb

    @property
    def dest_room(self):
        return load_by_key('room', self.destination)

    def glance(self, source, **_):
        if self.direction:
            source.display_line('Exit: {0}  {1}'.format(self.direction.desc, self.dest_room.title), EXIT_DISPLAY)
        else:
            source.display_line(self.title, EXIT_DISPLAY)

    def __call__(self, source, **_):
        if self.instanced:
            instance = next_instance()
            destination = instance.get_room(self.destination)
        else:
            destination = self.dest_room
        source.change_env(destination)
