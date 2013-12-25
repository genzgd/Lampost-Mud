from lampost.datastore.dbo import DBOMap
from lampost.lpflavor.attributes import ATTR_LIST, POOL_MAP
from lampost.lpflavor.combat import AttackTemplate
from lampost.lpflavor.entity import EntityLP

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):
    dbo_fields = EntityLP.template_fields + ATTR_LIST + tuple(POOL_MAP.iterkeys()) + ('race', 'effects')

    race = 'unknown'

    def status_change(self):
        if self.session:
            self.session.update_status(self.display_status)
