'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO, DBOCollection
from room import Room
from mobile import MobileTemplate

class Reset(RootDBO):
    dbo_fields = ("reset_type", "item_id", "target_id", "params")
    def __init__(self, item_id, target_id, params=None):
        self.item_id = item_id
        self.target_id = target_id
        self.params = params
        
Reset.dbo_base_class = Reset
    
    
class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name", "next_room_id", "next_mob_id", "owner_id")
    dbo_collections = DBOCollection("rooms", Room, "room"), DBOCollection("resets", Reset),\
        DBOCollection("mobiles", MobileTemplate, "mobile"), 
    
    next_room_id = 1
    next_mob_id = 1
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.rooms = []
        self.resets = []
        self.mobiles = []
        
    def get_room(self, room_id):
        for room in self.rooms:
            if room.dbo_id == room_id:
                return room;

Area.dbo_base_class = Area