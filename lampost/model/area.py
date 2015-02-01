from lampost.datastore.dbo import ParentDBO
from lampost.datastore.dbofield import DBOField
from lampost.gameops.script import Scriptable


class Area(ParentDBO, Scriptable):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_children_types = ['room', 'mobile', 'article']

    name = DBOField()
    desc = DBOField()
    next_room_id = DBOField(0)
