import sys
from lampost.context.resource import requires, inject
from lampost.datastore.dbo import RootDBO, DBORef, DBODict
from lampost.env.room import Room
from lampost.gameops.template import TemplateException
from lampost.mobile.mobile import MobileTemplate
from random import randint
from lampost.model.article import ArticleTemplate

inject(sys.modules[__name__], 'log')

@requires('dispatcher')
class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name", "next_room_id", "owner_id")
    dbo_collections = DBORef("rooms", Room, "room"),  DBORef("mobiles", MobileTemplate, "mobile"), \
        DBORef("articles", ArticleTemplate, "article")
    
    next_room_id = 1
    reset_time = 180
    reset_pulse = 20
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.rooms = DBODict()
        self.mobiles = DBODict()
        self.articles = DBODict()
        self.reset_wait = 0
    
    @property
    def first_room(self):
        return self.sorted_rooms[0]
        
    @property
    def sorted_rooms(self):
        return sorted(self.rooms.values(), key= lambda x:int(x.dbo_id.split(":")[1]))
        
    def get_room(self, room_id):
        return self.rooms.get(room_id)
        
    def get_mobile(self, mobile_id):
        if not ":" in mobile_id:
            mobile_id = ":".join([self.dbo_id, mobile_id])
        return self.mobiles.get(mobile_id)
        
    def get_article(self, article_id):
        if not ":" in article_id:
            article_id = ":".join([self.dbo_id, article_id])
        return self.articles.get(article_id)
                
    def on_loaded(self):
        self.reset()
        self.reset_wait = randint(-180, 0) #Start resets at staggered intervals 
        self.reset_reg = self.dispatcher.register_p(self.reset_pulse * 4, self.check_reset, self.reset_pulse * 2)
        
    def check_reset(self):
        self.reset_wait += self.reset_pulse
        if self.reset_wait >= self.reset_time:
            self.reset()
            
    def reset(self):
        debug("{0} Area resetting".format(self.dbo_id))
        self.reset_wait = 0
        for room in self.rooms.itervalues():
            room.reset(self)
        
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
            
    def create_mob(self, mobile_id, env):
        try:
            template = self.get_mobile(mobile_id)
            mob = template.create_instance()
            mob.enter_env(env)
        except KeyError:
            debug("No template for " + mobile_id)
        except TemplateException:
            pass
            
    def create_article(self, article_id, env):
        try:
            template = self.get_article(article_id)
            article = template.create_instance()
            article.enter_env(env)
        except KeyError:
            debug("No template for " + article_id)
        except TemplateException:
            pass
            
    def detach(self):
        if self.reset_reg:
            self.reset_reg.detach()
            