from lampost.datastore.dbo import RootDBO
from lampost.model.entity import Entity


class Player(Entity, RootDBO):
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Entity.dbo_fields + ("imm_level", "room_id", "home_room", "age",
                                      "user_id", "created", "last_login", "last_logout")
    imm_level = 0
    user_id = 0
    last_login = 0
    created = 0
    last_logout = 0
    age = 0
    build_mode = False
    rec_player = True

    def __init__(self, dbo_id):
        self.dbo_id = unicode(dbo_id).lower()
        self.target_id = self.dbo_id,
        self.name = dbo_id.capitalize()
        self.last_tell = None
        self.equip_slots = {}

    def on_loaded(self):
        if not self.desc:
            self.desc = "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def start(self):
        self.register_p(self.autosave, seconds=20)

    def rec_glance(self, source, **ignored):
        source.display_line("{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player"))

    def display_channel(self, message):
        if message.source != self:
            self.display_line(message.text, message.display)

    def display_line(self, text, display='default'):
        if text:
            self.session.display_line({'text': text, 'display': display})

    def output(self, output):
        self.session.append(output)

    def register_channel(self, channel):
        self.register(channel, self.display_channel)

    def rec_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.display)

    def get_score(self):
        score = {}
        return score

    def die(self):
        pass

    def detach(self):
        super(Player, self).detach()
        self.session = None

