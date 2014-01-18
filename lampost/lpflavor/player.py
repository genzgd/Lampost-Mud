from lampost.datastore.dbo import DBOField
from lampost.lpflavor.entity import EntityLP
from lampost.lpflavor.skill import SkillTemplate, BaseSkill

from lampost.model.player import Player


class PlayerLP(Player, EntityLP):

    race = DBOField('unknown')
    affinity = 'player'
    skills = DBOField({}, BaseSkill)
    can_die = True

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)
        EntityLP.__init__(self)
        self.auto_fight = False

    def on_loaded(self):
        super(PlayerLP, self).on_loaded()
        for skill in self.skills.viewvalues():
            self.add_skill(skill)

    def status_change(self):
        if not self.session:
            return
        status = self.display_status
        if self.last_opponent:
            status['opponent'] = self.last_opponent.display_status
            status['opponent']['name'] = self.last_opponent.name
        self.session.update_status(status)

    def die(self):
        if not self.can_die:
            self.display_line("You die.  Fortunately, you\'re immortal.")
            self.health = 1
            self.start_refresh()
            return

        self.health = 0
        self.display_line("Alas, you succumb to your injuries")
        self.status = 'dead'
        self.action = 0


