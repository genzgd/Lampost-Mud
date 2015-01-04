from lampost.datastore.dbofield import DBOField
from lampost.model.race import PlayerRace


class Archetype(PlayerRace):
    dbo_set_key = 'arch'


class PlayerRaceLP(PlayerRace):
    class_id = 'race'
    default_skills = DBOField([], 'default_skill')
