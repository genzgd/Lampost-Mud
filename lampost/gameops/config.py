from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO

@provides('config')
@requires('lsp', 'encode')
class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room', 'next_user_id')
    start_room = "immortal_citadel:0"
    title = "Lampost-Mud"
    description = "A fresh install of Lampost Mud"
    next_user_id = 1

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id

    def on_loaded(self):
        title = self.title.replace('"', '\\\"')
        title = title.replace("'", "\\'")
        title = title.replace("\n", "")
        description = self.description.replace('"', '\\\"')
        description = description.replace("'", "\\'")
        description = description.replace("\n", "")
        self.lsp.add_js("config.js", "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description))



