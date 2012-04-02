'''
Created on Feb 26, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO, DBOCollection

class Area(RootDBO):
    dbo_key_type = "area"
    dbo_set_key = "areas"
    dbo_fields = ("name",)
    dbo_collections = (DBOCollection("rooms", "room"))
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id
        self.rooms = []
