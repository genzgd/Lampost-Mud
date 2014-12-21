from lampost.datastore.dbo import DBOField
from lampost.model.race import PlayerRace


class Archetype(PlayerRace):
    dbo_set_key = 'arch'


class PLayerRaceLP(PlayerRace):
    class_id = 'race'
    default_skills = DBOField({})

    @property
    def template_refs(self):
        return self.default_skills.keys()
