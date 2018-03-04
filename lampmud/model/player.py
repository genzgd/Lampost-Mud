from lampost.di.resource import Injected, module_inject
from lampost.event.zone import Attachable
from lampost.gameops.target import TargetKeys
from lampost.meta.auto import AutoField
from lampost.db.dbo import SystemDBO
from lampost.db.dbofield import DBOField

log = Injected('log')
ev = Injected('dispatcher')
module_inject(__name__)


class Player(SystemDBO, Attachable):
    dbo_key_type = "player"
    dbo_set_key = "players"

    session = AutoField()

    user_id = DBOField(0)
    created = DBOField(0)
    imm_level = DBOField(0)
    last_login = DBOField(0)
    last_logout = DBOField(0)
    age = DBOField(0)
    room_id = DBOField()
    home_room = DBOField()
    instance_id = DBOField(0)
    instance_room_id = DBOField()
    group = AutoField()

    is_player = True
    can_die = True

    @property
    def edit_dto(self):
        dto = super().edit_dto
        dto['logged_in'] = "Yes" if self.session else "No"
        return dto

    @property
    def name(self):
        return self.dbo_id.capitalize()

    @property
    def location(self):
        try:
            return getattr(self.env, "title")
        except AttributeError:
            return "Unknown"

    def _on_loaded(self):
        if not self.desc:
            self.desc = "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def _on_attach(self):
        ev.register_p(self.autosave, seconds=20)
        self.active_channels = set()
        self.target_keys = TargetKeys(self.dbo_id)
        self.last_tell = None

    def _on_detach(self):
        self.session = None

    def check_logout(self):
        pass

    def glance(self, source, **_):
        source.display_line("{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player"))

    def display_line(self, text, display='default'):
        if text and self.session:
            self.session.display_line({'text': text, 'display': display})

    def output(self, output):
        if self.session:
            self.session.append(output)

    def receive_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.display)

    def die(self):
        pass


