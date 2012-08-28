from lampost.context.resource import provides
from lampost.datastore.dbo import RootDBO

__author__ = "Geoff"

@provides('config')
class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room')
    start_room = "immortal_citadel:0"
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id