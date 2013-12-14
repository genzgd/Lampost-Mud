from random import randint

from lampost.context.resource import requires, m_requires
from lampost.datastore.dbo import RootDBO
from lampost.env.room import Room
from lampost.model.mobile import MobileTemplate
from lampost.model.article import ArticleTemplate


m_requires('log', 'dispatcher', 'datastore',  __name__)


class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = "name", "desc", "next_room_id", "owner_id", "dbo_rev"

    next_room_id = 0
    dbo_rev = 0
    rooms = {}
    mobiles = {}
    articles = {}
    desc = ""

    reset_time = 180

    def coll_key(self, coll):
        return 'area_{}:{}'.format(coll, self.dbo_id)

    def on_loaded(self):
        for coll_type, coll_class in [('rooms', Room), ('mobiles', MobileTemplate), ('articles', ArticleTemplate)]:
            coll = {}
            setattr(self, coll_type, coll)
            for coll_id in fetch_set_keys(self.coll_key(coll_type)):
                coll[coll_id] = load_object(coll_class, coll_id)

    def add_coll_item(self, coll_type, item):
        coll = getattr(self, coll_type)
        coll[item.dbo_id] = item
        add_set_key(self.coll_key(coll_type), item.dbo_id)

    def del_coll_item(self, coll_type, item):
        coll = getattr(self, coll_type)
        del coll[item.dbo_id]
        delete_set_key(self.coll_key(coll_type), item.dbo_id)

    def start(self):
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

    def inc_next_room(self, room):
        while self.get_room(self.dbo_id + ':' + str(self.next_room_id)):
            self.next_room_id += 1
        save_object(self)

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
