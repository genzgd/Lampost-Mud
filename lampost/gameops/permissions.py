from lampost.context.resource import provides, requires
from lampost.player.player import Player
from lampost.util.lmutil import PermError

__author__ = 'Geoff'

@provides('perm', True)
@requires('datastore')
class Permissions(object):
    levels = {'supreme':100000, 'admin':10000, 'creator':1000}

    def has_perm(self, player, action):
        try:
            self.check_perm(player, action)
            return True
        except PermError:
            return False

    def check_perm(self, player, action):
        try:
            player_level = player.imm_level
        except AttributeError:
            try:
                player = player.player
                player_level = player.imm_level
            except AttributeError:
                raise PermError
        if player_level >= self.perm_level('supreme'):
            return
        if isinstance(action, int) and player_level > action:
            return
        named_level = self.levels.get(action, None)
        if named_level and player_level > named_level:
            return
        imm_level = getattr(action, 'imm_level', None)
        if imm_level and player_level >= imm_level:
            return
        owner_id = getattr(action, 'owner_id', None)
        if not owner_id or player.dbo_id == owner_id:
            return
        owner = self.datastore.load_object(Player, owner_id)
        if owner and player_level > owner.imm_level:
            return
        raise PermError

    def perm_level(self, label):
        return self.levels.get(label, self.levels['admin'])


