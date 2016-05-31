from lampost.di.resource import Injected, module_inject
from lampost.db.dbofield import DBOField, DBOLField
from lampost.gameops.action import ActionError
from lampost.di.config import m_configured

from lampmud.env.room import Room
from lampmud.lpmud.attributes import base_pools, fill_pools
from lampmud.lpmud.entity import EntityLP, Skilled
from lampmud.lpmud.skill import add_skill
from lampmud.model.item import ItemDBO

from lampmud.model.player import Player

ev = Injected('dispatcher')
db = Injected('datastore')
module_inject(__name__)

m_configured(__name__, 'default_start_room')


class PlayerLP(Player, EntityLP, ItemDBO, Skilled):
    dbo_key_type = 'player'

    race = DBOLField(dbo_class_id='race')
    touchstone = DBOField()
    size = DBOField('medium')
    affinity = 'player'
    can_die = True

    def on_created(self):
        for attr_name, start_value in self.race.base_attrs.items():
            setattr(self, attr_name, start_value)
            setattr(self, 'perm_{}'.format(attr_name), start_value)
        fill_pools(self)
        if self.race.start_instanced:
            self.instance_room_id = self.race.start_room.dbo_id
            self.room_id = None
        else:
            self.room_id = self.race.start_room.dbo_id

    def on_loaded(self):
        self.auto_fight = False
        for skill in self.skills.values():
            self._apply_skill(skill)

    def on_attach(self):
        if self.race:
            for default_skill in self.race.default_skills:
                if default_skill.skill_template.dbo_key not in self.skills.keys():
                    add_skill(default_skill.skill_template, self, default_skill.skill_level, 'race')

        base_pools(self)
        self.status_change()
        self.start_refresh()

    def check_logout(self):
        if self.last_opponent:
            self.display_line("You are in life threatening combat!  You can't log out right now.", 'combat')
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

        self.display_line("Alas, you succumb to your injuries.", 'combat')
        self.display_line("Unless other help intercedes, you will be returned to your last touchstone in 90 seconds.<br/>"
                          "You may hasten the end if you 'abandon' all hope of assistance.", 'system')
        self._death_effects()
        self._bind_pulse = ev.register_once(self.resurrect, seconds=90)
        self.status_change()

    def resurrect(self, auto=True):
        ev.unregister(self._bind_pulse)
        del self._bind_pulse
        res_room = None
        if self.touchstone:
            res_room = db.load_object(self.touchstone, Room)
        if not res_room:
            res_room = db.load_object(default_start_room, Room)
        self.change_env(res_room)
        self.display_line("With a sick feeling, you return to consciousness")
        self.status = 'ok'
        self.heath = 1
        self.start_refresh()
