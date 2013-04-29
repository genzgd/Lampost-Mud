from random import randint

from lampost.context.resource import requires, m_requires
from lampost.datastore.dbo import RootDBO, DBORef, DBODict
from lampost.env.room import Room
from lampost.model.mobile import MobileTemplate
from lampost.model.article import ArticleTemplate


m_requires('log', __name__)


@requires('dispatcher')
class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name", "next_room_id", "owner_id", "dbo_rev")
    dbo_collections = DBORef("rooms", Room, "room"),  DBORef("mobiles", MobileTemplate, "mobile"), \
        DBORef("articles", ArticleTemplate, "article")

    next_room_id = 0
    dbo_rev = 0

    reset_time = 180  # reset every 3 minutes
    reset_pulse = 20  # we get the reset pulse every 20 seconds

    def __init__(self, dbo_id):
        super(Area, self).__init__(dbo_id)
        self.rooms = DBODict()
        self.mobiles = DBODict()
        self.articles = DBODict()
        self.reset_wait = randint(-180, 0)  # Start resets at staggered intervals

    def start(self):
        self.reset()
        self.reset_reg = self.register_p(self.check_reset, seconds=self.reset_pulse, randomize=10)

    @property
    def first_room(self):
        return self.sorted_rooms[0]

    @property
    def sorted_rooms(self):
        return sorted(self.rooms.values(), key=lambda x: int(x.dbo_id.split(":")[1]))

    def get_room(self, room_id):
        return self.rooms.get(room_id)

    def inc_next_room(self, room_id):
        if self.next_room_id == room_id:
            while self.get_room(self.dbo_id + ':' + str(self.next_room_id)):
                self.next_room_id += 1

    def get_mobile(self, mobile_id):
        if not ":" in mobile_id:
            mobile_id = ":".join([self.dbo_id, mobile_id])
        return self.mobiles.get(mobile_id)

    def get_article(self, article_id):
        if not ":" in article_id:
            article_id = ":".join([self.dbo_id, article_id])
        return self.articles.get(article_id)

    def check_reset(self):
        self.reset_wait += self.reset_pulse
        if self.reset_wait >= self.reset_time:
            self.reset()

    def reset(self):
        debug("{0} Area resetting".format(self.dbo_id))
        self.reset_wait = 0
        for room in self.rooms.itervalues():
            room.reset()

    def find_mobile_resets(self, mobile_id):
        for room in self.rooms:
            for mobile_reset in room.mobile_resets:
                if mobile_reset.mobile_id == mobile_id:
                    yield room, mobile_reset

    def find_article_resets(self, article_id):
        for room in self.rooms:
            for article_reset in room.article_resets:
                if article_reset.article_id == article_id:
                    yield room, article_reset

