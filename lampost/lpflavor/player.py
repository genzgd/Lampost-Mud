from lampost.lpflavor.attributes import ATTR_LIST

from lampost.model.player import Player


class PlayerLP(Player):
    dbo_fields = Player.dbo_fields + ("race",) + ATTR_LIST + tuple(['{}_perm'.format(attr) for attr in ATTR_LIST])

    def __init__(self, dbo_id):
        super(PlayerLP, self).__init__(dbo_id)