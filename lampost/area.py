'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO, DBORef, DBODict
from room import Room
from mobile import MobileTemplate
from random import randint
from coreobj.template import TemplateException


class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name", "next_room_id", "next_mob_id", "owner_id")
    dbo_collections = DBORef("rooms", Room, "room"),  DBORef("mobiles", MobileTemplate, "mobile")
    
    next_room_id = 1
    next_mob_id = 1
    reset_time = 180
    reset_pulse = 20
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.rooms = DBODict()
        self.mobiles = DBODict()
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
        return self.mobiles.get(mobile_id)
                
    def on_loaded(self):
        self.reset()
        self.reset_wait = randint(-180, 0) #Start resets at staggered intervals 
        self.dispatcher.register_p(self.reset_pulse * 4, self.check_reset, self.reset_pulse * 2)
        
    def check_reset(self):
        self.reset_wait += self.reset_pulse
        if self.reset_wait >= self.reset_time:
            self.reset()
            
    def reset(self):
        self.dispatcher.dispatch("debug", "{0} Area resetting".format(self.dbo_id))
        self.reset_wait = 0
        for room in self.rooms.itervalues():
            room.reset(self)
            
    def create_mob(self, mobile_id, env):
        try:
            template = self.get_mobile(mobile_id)
            mob = template.create_instance()
            mob.enter_env(env)
        except KeyError:
            self.dispatcher.dispatch("debug", "No template for " + mobile_id)
        except TemplateException:
            pass
            