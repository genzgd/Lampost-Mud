from lampost.model.race import PlayerRace


class Archetype(PlayerRace):
    dbo_set_key = 'arch'


class PLayerRaceLP(PlayerRace):
    dbo_fields = 'default_skills',

    default_skills = {}
