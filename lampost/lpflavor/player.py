from lampost.datastore.dbo import DBOField
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillTemplate

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):

    race = DBOField('unknown')
    skills = DBOField({}, SkillTemplate)


    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)
        EntityLP.__init__(self)

    def status_change(self):
        if self.session:
            self.session.update_status(self.display_status)
