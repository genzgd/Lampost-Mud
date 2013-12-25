from lampost.datastore.dbo import RootDBO

base_attr_value = 5


class PlayerRace(RootDBO):
    dbo_key_type = "race"
    dbo_set_key = "races"
    dbo_fields = "dbo_rev", "name", "desc", "base_attrs"
    dbo_rev = 0

    attr_list = []
    name = "Unnamed"
    desc = ""
    base_attrs = {}

    def on_created(self):
        if not self.base_attrs:
            self.base_attrs = {attr_name: base_attr_value for attr_name in self.attr_list}
