'''
Created on Apr 27, 2012

@author: Geoff
'''
from lampost.datastore.dbo import RootDBO

class Config(RootDBO):
    dbo_key_type = "config"
    dbo_id = "config"
    dbo_fields = "start_room", 
    start_room = "immortal_citadel:0"
    
    def __init__(self, config_id = "config"):
        pass