from lampost.lpflavor.attributes import attr_list

from lampost.model.player import Player


class PlayerLP(Player):
    dbo_fields = Player.dbo_fields + attr_list

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)

