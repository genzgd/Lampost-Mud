from lampost.datastore.dbo import DBOMap
from lampost.lpflavor.attributes import ATTR_LIST, POOL_MAP
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillStatus

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):
    dbo_fields = EntityLP.template_fields + ATTR_LIST + tuple(POOL_MAP.iterkeys()) + ('race', 'effects')
    dbo_maps = DBOMap("skills", SkillStatus),

    race = 'unknown'

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)
        self.defenses = []

    def status_change(self):
        if self.session:
            self.session.update_status(self.display_status)



