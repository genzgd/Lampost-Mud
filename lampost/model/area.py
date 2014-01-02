from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.env.room import Room


m_requires('log', 'dispatcher', 'datastore',  __name__)


class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"

    name = DBOField()
    desc = DBOField()
    next_room_id = DBOField(0)
    owner_id = DBOField()
    dbo_rev = DBOField(0)

    reset_time = 180

    def on_loaded(self):
        self.rooms = {room.dbo_id: room for room in load_object_set(Room, 'area_rooms:{}'.format(self.dbo_id))}
        self.reset()
        register_p(self.reset, seconds=self.reset_time, randomize=self.reset_time)

    @property
    def first_room(self):
        return sorted(self.rooms.values(), key=lambda x: int(x.dbo_id.split(":")[1]))[0]

    def add_room(self, room):
        self.rooms[room.dbo_id] = room
        while self.rooms.get(self.dbo_id + ':' + str(self.next_room_id)):
            self.next_room_id += 1
        save_object(self)

    def reset(self):
        debug("{0} Area resetting".format(self.dbo_id))
        for room in self.rooms.itervalues():
            room.reset()
