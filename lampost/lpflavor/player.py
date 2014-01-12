from lampost.datastore.dbo import DBOField
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillTemplate, BaseSkill

from lampost.model.player import Player

class PlayerLP(Player, EntityLP):

    race = DBOField('unknown')
    skills = DBOField({}, BaseSkill)
    can_die = True

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)
        EntityLP.__init__(self)
        self.auto_fight = False

    def status_change(self):
        if self.session:
            self.session.update_status(self.display_status)

    def die(self):
        if not self.can_die:
            self.display_line("You die.  Fortunately, you\'re immortal.")
            self.health = 1
            return

        self.health = 0
        self.display_line("Alas, you succumb to your injuries")
        self.status = 'dead'
        self.action = 0
