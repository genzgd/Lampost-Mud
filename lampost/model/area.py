from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.env.room import Room


m_requires('log', 'dispatcher', 'datastore',  __name__)

reset_time = 180


class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"

    name = DBOField()
    desc = DBOField()
    next_room_id = DBOField(0)
    owner_id = DBOField()
    dbo_rev = DBOField(0)
    instanced = DBOField(False)

    def on_loaded(self):
        register_p(self.reset, seconds=reset_time, randomize=reset_time)

    @property
    def room_keys(self):
        return fetch_set_keys('area_rooms:{}'.format(self.dbo_id))

    @property
    def sorted_keys(self):
        return sorted(self.room_keys,  key=lambda x: int(x.split(":")[1]))

    @property
    def first_room(self):
        return self.load_room(self.sorted_keys[0], instance)

    def load_room(self, dbo_id, instance=0):
        room = load_object(Room, dbo_id)
        if instance:
            clone = get_dbo_class('room')()
            clone.template = room
            clone.instance = instance
            return clone
        return room

    def add_room(self, room):
        while self.rooms.get(self.dbo_id + ':' + str(self.next_room_id)):
            self.next_room_id += 1
        save_object(self)

    def reset(self):
        debug("{0} Area resetting".format(self.dbo_id))
        for room_id in self.room_keys:
            loaded = load_cached('room', room_id)
            if loaded:
                loaded.reset()
