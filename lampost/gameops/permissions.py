from lampost.context.resource import provides, m_requires
from lampost.util.lmutil import PermError

m_requires(__name__, 'datastore')


@provides('perm', True)
class Permissions():
    levels = {'supreme': 100000, 'admin': 10000, 'creator': 1000, 'none': 0, 'player': 0}

    def __init__(self):
        self.rev_levels = {}
        self.immortals = {}
        for name, level in self.levels.items():
            self.rev_levels[level] = name

    def _post_init(self):
        self.immortals = get_all_hash('immortals')

    def perm_name(self, num_level):
        return self.rev_levels.get(num_level, 'none')

    def update_immortal_list(self, player):
        if player.imm_level:
            set_db_hash('immortals', player.dbo_id, player.imm_level)
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
        if getattr(action, 'unprotected', None):
            return
        if isinstance(action, int):
            perm_required = action
        elif action in self.levels:
            perm_required = self.levels[action]
        else:
            imm_level = getattr(action, 'imm_level', 0)
            perm_required = self.levels.get(imm_level, imm_level)
        owner_id = getattr(action, 'owner_id', None)
        if owner_id:
            perm_required = max(self.immortals.get(owner_id, self.levels['admin']) + 1, perm_required)
        if not perm_required:
            return
        try:
            player_level = player.imm_level
        except AttributeError:
            try:
                player = player.player
                player_level = player.imm_level
            except AttributeError:
                raise PermError
        if player_level >= self.levels['supreme']:
            return
        if player_level >= perm_required:
            return
        if player.dbo_id == owner_id:
            return
        raise PermError

    def perm_level(self, label):
        return self.levels.get(label, self.levels['admin'])

    def perm_to_level(self, label):
        return self.levels.get(label)
