from lampost.di.resource import m_requires
from lampost.meta.auto import AutoField
from lampost.db.dbo import KeyDBO, SystemDBO
from lampost.db.dbofield import DBOField

from lampmud.model.item import Attached

m_requires(__name__, 'log', 'dispatcher')


class Player(KeyDBO, SystemDBO, Attached):
    dbo_key_type = "player"
    dbo_set_key = "players"

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

    def on_loaded(self):
        self.target_keys = {(self.dbo_id,)}
        self.last_tell = None
        self.active_channels = set()
        self.session = None
        if not self.desc:
            self.desc = "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def check_logout(self):
        pass

    def start(self):
        register_p(self.autosave, seconds=20)

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

    def on_detach(self):
        self.session = None
