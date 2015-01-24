from lampost.datastore.dbo import KeyDBO, DBOAccess
from lampost.datastore.dbofield import DBOField, DBOLField

base_attr_value = 5


class PlayerRace(DBOAccess, KeyDBO):
    dbo_key_type = "race"
    dbo_set_key = "races"

    attr_list = []

    name = DBOField("Unnamed")
    desc = DBOField('')
    base_attrs = DBOField({})
    start_room = DBOLField(dbo_class_id='room')
    start_instanced = DBOField(False)

    @property
    def new_dto(self):
        dto = super().new_dto
        dto['base_attrs'] = {attr_name: base_attr_value for attr_name in self.attr_list}
        return dto