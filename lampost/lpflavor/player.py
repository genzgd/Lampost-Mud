from lampost.context.resource import m_requires
from lampost.datastore.dbofield import DBOField, DBOLField
from lampost.env.room import Room
from lampost.gameops.action import ActionError
from lampost.lpflavor.entity import EntityLP
from lampost.model.item import BaseItem

from lampost.model.player import Player


m_requires(__name__, 'dispatcher', 'datastore', 'config_manager')


class PlayerLP(Player, EntityLP, BaseItem):
    dbo_key_type = 'player'

    race = DBOLField(dbo_class_id='race')
    affinity = 'player'
    skills = DBOField({}, 'untyped')
    touchstone = DBOField()
    can_die = True
    size = DBOField('medium')

    def __init(self):
        super().__init__()
        self.auto_fight = False

    def on_loaded(self):
        for skill in self.skills.values():
            self._apply_skill(skill)

    def check_logout(self):
        if self.last_opponent:
            self.display_line("You are in life threatening combat!  You can't log out right now.", "combat")
            if self.imm_level:
                self.display_line("(You might want to consider imposing 'peace.')")
            raise ActionError()

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
            self.broadcast(s="You die.  Fortunately, you're immortal.", e="{n} examines {s} otherwise fatal wounds and shrugs.")
            self.health = 1
            self.start_refresh()
            return

        self.display_line("Alas, you succumb to your injuries.", "combat")
        self.display_line("Unless other help intercedes, you will be returned to your last touchstone in 90 seconds.<br/>"
                          "You may hasten the end if you 'abandon' all hope of assistance.", "system")
        self._death_effects()
        self._bind_pulse = register_once(self.resurrect, seconds=90)
        self.status_change()

    def resurrect(self, auto=True):
        unregister(self._bind_pulse)
        del self._bind_pulse
        res_room = None
        if self.touchstone:
            res_room = load_object(self.touchstone, Room)
        if not res_room:
            res_room = load_object(config_manager.start_room, Room)
        self.change_env(res_room)
        self.display_line("With a sick feeling, you return to consciousness")
        self.status = 'ok'
        self.heath = 1
        self.start_refresh()