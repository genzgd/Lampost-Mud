from lampost.datastore.dbo import RootDBO


class PlayerRace(RootDBO):
    dbo_key_type = "race"
    dbo_set_key = "races"
    dbo_fields = "dbo_rev", "name", "desc", "base_attrs"
    dbo_rev = 0

    attr_list = []
    name = "Unnamed"
    desc = ""
    base_attr_value = 5

    def __init__(self, dbo_id):
        super(PlayerRace, self).__init__(dbo_id)
        self.base_attrs = {attr_name: self.base_attr_value for attr_name in self.attr_list}
