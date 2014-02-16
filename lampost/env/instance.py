from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import convert_verbs

m_requires('datastore', __name__)

instance_id = 0


def next_instance():
    global instance_id
    instance_id += 1
    return AreaInstance(instance_id)


class AreaInstance(object):
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
        for room in self.rooms.viewvalues():
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
    destination = DBOField()
    edit_required = DBOField(True)

    target_class = None

    def on_loaded(self):
        super(Feature, self).on_loaded()
        self.verbs = convert_verbs(self.verb)
        if not self.title:
            self.title = self.verb

    def __call__(self, source, **ignored):
        instance = next_instance()
        source.change_env(instance.get_room(self.destination))


