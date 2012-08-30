from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO

__author__ = "Geoff"

@provides('config')
@requires('lsp')
class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room')
    start_room = "immortal_citadel:0"
    title = "Lampost-Mud"
    description = "A fresh install of Lampost Mud"
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id

    def on_loaded(self):
        self.lsp.add_js("config.js", "var lampost_config = {{title:'{0}', description:'{1}'}};".format(self.title, self.description))



