from lampost.datastore.dbo import DBOField, RootDBO
from lampost.gameops.script import Scriptable


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
