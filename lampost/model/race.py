from lampost.datastore.dbo import KeyDBO, DBOAccess
from lampost.datastore.dbofield import DBOField, DBOLField
from lampost.gameops.config import m_configured

m_configured(__name__, 'base_attr_value', 'default_start_room')


class PlayerRace(DBOAccess, KeyDBO):
    dbo_key_type = "race"
    dbo_set_key = "races"

    attr_list = []

    name = DBOField("Unnamed")
    desc = DBOField('')
    base_attrs = DBOField({})
    start_room = DBOLField(default_start_room, 'room')
    start_instanced = DBOField(False)

    @classmethod
    def new_dto(cls):
        dto = super().new_dto()
        dto['base_attrs'] = {attr_name: base_attr_value for attr_name in cls.attr_list}
        return dto
