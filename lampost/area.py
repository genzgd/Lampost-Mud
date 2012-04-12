'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO, DBOCollection
from room import Room

class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name", "next_room_id", "owner_id")
    dbo_collections = DBOCollection("rooms", Room, "room"),
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.rooms = []
        
    def get_room(self, room_id):
        for room in self.rooms:
            if room.dbo_id == room_id:
                return room;

Area.dbo_base_class = Area