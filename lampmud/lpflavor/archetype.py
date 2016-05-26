from lampost.db.dbofield import DBOField

from lampmud.model.race import PlayerRace


class Archetype(PlayerRace):
    dbo_set_key = 'arch'


class PLayerRaceLP(PlayerRace):
    class_id = 'race'
    default_skills = DBOField([], 'default_skill')
