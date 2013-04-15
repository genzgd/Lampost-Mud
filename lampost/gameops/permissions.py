from lampost.context.resource import provides, m_requires
from lampost.model.player import Player
from lampost.util.lmutil import PermError

m_requires('datastore', __name__)

@provides('perm', True)
class Permissions(object):
    levels = {'supreme': 100000, 'admin': 10000, 'creator': 1000, 'none': 0}

    def __init__(self):
        self.rev_levels = {}
        self.immortals = {}
        for name, level in self.levels.iteritems():
            self.rev_levels[level] = name

    def _post_init(self):
        self.immortals = get_all_index('immortals')

    def perm_name(self, num_level):
        return self.rev_levels.get(num_level, 'none')

    def update_immortal_list(self, player):
        if player.imm_level:
            set_index('immortals', player.dbo_id, player.imm_level)
            self.immortals[player.dbo_id] = player.imm_level
        else:
            delete_index('immortals', player.dbo_id)
            try:
                del self.immortals[player.dbo_id]
            except KeyError:
                pass

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
        if player_level > self.immortals.get(owner_id, 0):
            return
        raise PermError

    def perm_level(self, label):
        return self.levels.get(label, self.levels['admin'])

    def perm_to_level(self, label):
        return self.levels.get(label)