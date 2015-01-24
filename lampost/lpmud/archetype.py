from lampost.context.config import m_configured
from lampost.datastore.dbo import KeyDBO, DBOAccess
from lampost.datastore.dbofield import DBOField, DBOLField

m_configured(__name__, 'base_attr_value', 'attributes', 'default_start_room')


class Archetype(DBOAccess, KeyDBO):
    dbo_key_type = 'archetype'
    dbo_set_key = 'archetypes'

    name = DBOField("Unnamed")
    desc = DBOField('')
    base_attrs = DBOField({})


class PlayerRace(Archetype):
    dbo_key_type = "race"
    dbo_set_key = "races"

    default_skills = DBOField([], 'default_skill')
    start_room = DBOLField(dbo_class_id='room')
    start_instanced = DBOField(False)

    @classmethod
    def new_dto(cls):
        dto = super().new_dto()
        dto['start_room'] = default_start_room
        dto['base_attrs'] = {attr['dbo_id']: base_attr_value for attr in attributes}
        return dto


