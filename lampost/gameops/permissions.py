from lampost.context.resource import provides, requires
from lampost.model.player import Player
from lampost.util.lmutil import PermError

@provides('perm', True)
@requires('datastore')
class Permissions(object):
    levels = {'supreme':100000, 'admin':10000, 'creator':1000, 'none':0}

    def __init__(self):
        self.rev_levels = {}
        for name, level in self.levels.iteritems():
            self.rev_levels[level] = name

    def perm_name(self, num_level):
        return self.rev_levels.get(num_level, 'none')

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
        if isinstance(action, int) and player_level < action:
            raise PermError
        named_level = self.levels.get(action, None)
        if named_level and player_level < named_level:
            raise PermError
        imm_level = getattr(action, 'imm_level', None)
        if imm_level and player_level < imm_level:
            raise PermError
        owner_id = getattr(action, 'owner_id', None)
        if not owner_id or player.dbo_id == owner_id:
            return
        owner = self.datastore.load_object(Player, owner_id)
        if owner and player_level > owner.imm_level:
            return
        raise PermError

    def perm_level(self, label):
        return self.levels.get(label, self.levels['admin'])

