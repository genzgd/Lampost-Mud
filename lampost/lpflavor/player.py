from lampost.datastore.dbo import DBOMap, DBOList
from lampost.lpflavor.attributes import ATTR_LIST, POOL_LIST
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillStatus, SkillEffect

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):
    dbo_fields = Player.dbo_fields + EntityLP.dbo_fields + ATTR_LIST + tuple(['perm_{}'.format(attr) for attr in ATTR_LIST]) + POOL_LIST + ('race',)
    dbo_maps = DBOMap("skills", SkillStatus),
    dbo_lists = DBOList('effects', SkillEffect),

    race = 'unknown'
    health = 0
    stamina = 0
    mental = 0
    action = 0

    def action_priority(self, action):
        return -len(followers)