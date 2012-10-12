from lampost.datastore.dbo import RootDBO
from lampost.dto.display import DisplayLine
from lampost.dto.rootdto import RootDTO
from lampost.model.creature import Creature

class Player(Creature, RootDBO):
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level", "room_id", "home_room", "age",
                                        "user_id", "created", "last_login", "last_logout")
    imm_level = 0
    user_id = 0
    last_login = 0
    created = 0
    last_logout = 0
    age = 0
    build_mode = False

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id.lower()
        self.target_id = self.dbo_id,
        self.name = dbo_id.capitalize()
        self.last_tell = None
        self.equip_slots = {}

    def on_loaded(self):
        pass

    def start(self):
        self.register_p(self.autosave, seconds=20)

    def long_desc(self, observer):
        if self.desc:
            return self.desc
        return "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."

    def short_desc(self, observer):
        return "{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player")


    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)

    def display_line(self, text, color=0x000000):
        if text:
            self.session.display_line(DisplayLine(text, color))

    def output(self, output):
        self.session.append(output)

    def register_channel(self, channel):
        self.register(channel, self.display_channel)

    def rec_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.color)

    def get_score(self):
        score = RootDTO()
        return score

    def die(self):
        pass

    def detach(self):
        super(Player, self).detach()
        self.session = None

