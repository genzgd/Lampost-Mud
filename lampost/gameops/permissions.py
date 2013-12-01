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
        for key, value in self.immortals.iteritems():
            self.immortals[key] = int(value)

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
        perm_required = 0
        if isinstance(action, int):
            perm_required = action
        elif action in self.levels:
            perm_required = self.levels[action]
        perm_required = max(getattr(action, 'imm_level', 0), perm_required)
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
