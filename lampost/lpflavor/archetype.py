from lampost.datastore.dbo import DBOField
from lampost.model.race import PlayerRace


class Archetype(PlayerRace):
    dbo_set_key = 'arch'


class PLayerRaceLP(PlayerRace):
    default_skills = DBOField({})
