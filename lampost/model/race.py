from lampost.datastore.dbo import KeyDBO, DBOAccess
from lampost.datastore.dbofield import DBOField

base_attr_value = 5


class PlayerRace(KeyDBO, DBOAccess):
    dbo_key_type = "race"
    dbo_set_key = "races"

    attr_list = []

    name = DBOField("Unnamed")
    desc = DBOField('')
    base_attrs = DBOField({})
    start_room = DBOField()
    start_room_instanced = DBOField(False)

    def on_created(self):
        if not self.base_attrs:
            self.base_attrs = {attr_name: base_attr_value for attr_name in self.attr_list}
        return self
