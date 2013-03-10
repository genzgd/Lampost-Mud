from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO

@provides('config')
class Config(RootDBO):
    dbo_key_type = "config"
    dbo_fields = ('title', 'description', 'start_room', 'next_user_id', 'auto_imm_level')
    title = "Lampost (New Install)"
    description = "A fresh install of Lampost Mud"
    next_user_id = 1
    auto_imm_level = 0

    def __init__(self, dbo_id):
        self.dbo_id = dbo_id



