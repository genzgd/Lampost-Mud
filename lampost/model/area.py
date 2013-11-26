from random import randint

from lampost.context.resource import requires, m_requires
from lampost.datastore.dbo import RootDBO, DBOMap
from lampost.env.room import Room
from lampost.model.mobile import MobileTemplate
from lampost.model.article import ArticleTemplate


m_requires('log', 'dispatcher', __name__)


class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = "name", "next_room_id", "owner_id", "dbo_rev"
    dbo_maps = DBOMap("rooms", Room, "room"),  DBOMap("mobiles", MobileTemplate, "mobile"), \
        DBOMap("articles", ArticleTemplate, "article")

    next_room_id = 0
    dbo_rev = 0
    rooms = {}
    mobiles = {}
    articles = {}

    reset_time = 180

    def start(self):
        for room_id in [room_id for room_id, room in self.rooms.iteritems() if not room]:
            warn("Invalid room: {} -- removing from Area Object".format(room_id))
            del self.rooms[room_id]
        self.reset()
        register_p(self.reset, seconds=self.reset_time, randomize=self.reset_time)

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

    def reset(self):
        debug("{0} Area resetting".format(self.dbo_id))
        for room in self.rooms.itervalues():
            room.reset()

    def find_mobile_resets(self, mobile_id):
        for room in self.rooms.itervalues():
            for mobile_reset in room.mobile_resets:
                if mobile_reset.mobile_id == mobile_id:
                    yield room, mobile_reset

    def find_article_resets(self, article_id):
        for room in self.rooms.itervalues():
            for article_reset in room.article_resets:
                if article_reset.article_id == article_id:
                    yield room, article_reset

