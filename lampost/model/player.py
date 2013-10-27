from collections import defaultdict
from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO
from lampost.model.entity import Entity

m_requires('log', __name__)


class Player(RootDBO):
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = "imm_level", "room_id", "home_room", "age", "user_id", "created", "last_login", "last_logout"

    imm_level = 0
    user_id = 0
    last_login = 0
    created = 0
    last_logout = 0
    age = 0
    build_mode = False
    rec_player = True

    def __init__(self, dbo_id):
        super(Player, self).__init__(dbo_id)
        self.target_id = self.dbo_id,
        self.name = self.dbo_id.capitalize()
        self.last_tell = None
        self.equip_slots = {}
        self.soul = defaultdict(set)
        self.active_channels = []

    def on_loaded(self):
        if not self.desc:
            self.desc = "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def start(self):
        self.register_p(self.autosave, seconds=20)

    def rec_glance(self, source, **ignored):
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
        self.enhance_soul(channel)
        self.active_channels.append(channel.id)

    def unregister_channel(self, channel):
        self.diminish_soul(channel)
        try:
            self.active_channels.remove(channel.id)
        except ValueError:
            warn("Removing channel {} not in list".format(channel.display), self)

    def rec_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.display)

    def rec_follow(self, source, **ignored):
        self.followers.add(source)
        source.broadcast(s="You start following {N}.", t="{n} starts following you.", e="{n} starts following {N}.", target=self)

    def get_score(self):
        score = {}
        return score

    def die(self):
        pass

    def detach(self):
        super(Player, self).detach()
        self.session = None

