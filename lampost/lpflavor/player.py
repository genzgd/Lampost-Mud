from lampost.datastore.dbo import DBORef
from lampost.lpflavor.attributes import ATTR_LIST, POOL_LIST
from lampost.lpflavor.entity import EntityLP

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):
    dbo_fields = Player.dbo_fields + EntityLP.dbo_fields + ATTR_LIST + tuple(['perm_{}'.format(attr) for attr in ATTR_LIST]) + POOL_LIST + ('race',)

    race = 'unknown'
    health = 0
    stamina = 0
    mental = 0
    action = 0

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)
        self.effects = []
        self.skills = {}