from lampost.datastore.dbo import ParentDBO
from lampost.datastore.dbofield import DBOField


class Area(ParentDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_children_types = ['room', 'mobile', 'article', 'script']

    name = DBOField()
    desc = DBOField()
    next_room_id = DBOField(0)
