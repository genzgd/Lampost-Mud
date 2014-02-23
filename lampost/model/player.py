from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBOField

m_requires('log', 'dispatcher', __name__)


class Player(RootDBO):
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

    is_player = True
    can_die = True

    def __init__(self, dbo_id):
        super(Player, self).__init__(dbo_id)
        self.target_keys = {(self.dbo_id,)}
        self.last_tell = None
        self.active_channels = set()

    @property
    def dto_value(self):
        dto_value = super(Player, self).dto_value
        dto_value['logged_in'] = "Yes" if hasattr(self, 'session') else "No"
        return dto_value

    @property
    def name(self):
        return self.dbo_id.capitalize()

    def on_loaded(self):
        if not self.desc:
            self.desc = "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def check_logout(self):
        pass

    def start(self):
        register_p(self.autosave, seconds=20)

    def glance(self, source, **_):
        source.display_line("{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player"))

    def display_line(self, text, display='default'):
        if not text:
            return
        try:
            self.session.display_line({'text': text, 'display': display})
        except AttributeError:
            pass

    def output(self, output):
        self.session.append(output)

    def register_channel(self, channel):
        self.active_channels.add(channel)
        self.enhance_soul(channel)

    def unregister_channel(self, channel):
        try:
            self.active_channels.remove(channel)
            self.diminish_soul(channel)
        except ValueError:
            warn("Removing channel {} not in list".format(channel.display), self)

    def receive_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.display)

    def die(self):
        pass

    def detach(self):
        super(Player, self).detach()
        for channel in self.active_channels.copy():
            self.unregister_channel(channel)
        self.session = None
