from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBO
from lampost.gameops.script import Scriptable


m_requires(__name__, 'log', 'datastore')


class Area(RootDBO, Scriptable):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_children_types = ['room', 'mobile', 'article', 'script']

    name = DBOField()
    desc = DBOField()
    next_room_id = DBOField(0)
    owner_id = DBOField()
    dbo_rev = DBOField(0)
    unprotected = DBOField(False)

    def add_room(self):
        next_id = 0
        sorted_ids = self.dbo_child_keys('room')
        if sorted_ids:
            next_id = int(sorted_ids[0].split(":")[1])
        for dbo_id in sorted_ids:
            room_id = int(dbo_id.split(':')[1])
            if room_id == next_id:
                next_id += 1
            else:
                break
        self.next_room_id = next_id
        save_object(self)
