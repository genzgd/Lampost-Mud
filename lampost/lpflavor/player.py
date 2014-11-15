from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.env.room import Room
from lampost.gameops.action import ActionError
from lampost.gameops.display import SYSTEM_DISPLAY, COMBAT_DISPLAY
from lampost.lpflavor.entity import EntityLP

from lampost.model.player import Player


m_requires(__name__, 'dispatcher', 'datastore', 'config_manager')


class PlayerLP(Player, EntityLP):
    dbo_key_type = 'player'

    race = DBOField('human')
    affinity = 'player'
    skills = DBOField({}, 'skill_inst')
    touchstone = DBOField()
    can_die = True

    def __init__(self, dbo_id):
        super().__init__(dbo_id)
        self.auto_fight = False

    def on_loaded(self):
        for skill in self.skills.values():
            self.add_skill(skill)

    def check_logout(self):
        if self.last_opponent:
            raise ActionError("You can't log out right now.", COMBAT_DISPLAY)

    def status_change(self):
        if not self.session:
            return
        status = self.display_status
        if self.last_opponent and self.last_opponent.env == self.env:
            status['opponent'] = self.last_opponent.display_status
            status['opponent']['name'] = self.last_opponent.name
        else:
            status['opponent'] = None
        self.session.update_status(status)

    def die(self):
        if not self.can_die:
            self.display_line("You die.  Fortunately, you\'re immortal.")
            self.health = 1
            self.start_refresh()
            return

        self.display_line("Alas, you succumb to your injuries.", COMBAT_DISPLAY)
        self.display_line("Unless other help intercedes, you will be returned to your last touchstone in 90 seconds.<br/>"
                          "You may hasten the end if you 'abandon' all hope of assistance.", SYSTEM_DISPLAY)
        self._death_effects()
        self._bind_pulse = register_once(self.resurrect, seconds=90)
        self.status_change()

    def resurrect(self, auto=True):
        unregister(self._bind_pulse)
        del self._bind_pulse
        res_room = None
        if self.touchstone:
            res_room = load_object(Room, self.touchstone)
        if not res_room:
            res_room = load_object(Room, config_manager.start_room)
        self.change_env(res_room)
        self.display_line("With a sick feeling, you return to consciousness")
        self.status = 'ok'
        self.heath = 1
        self.start_refresh()