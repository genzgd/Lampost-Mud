from lampost.context.resource import provides, m_requires
from lampost.util.lputil import PermError

m_requires(__name__, 'datastore', 'context')

imm_levels = {'supreme': 100000, 'founder': 50000, 'admin': 10000, 'senior': 2000, 'creator': 1000, 'player': 0}


@provides('perm', True)
class Permissions():
    system_accounts = ['lampost']
    system_level = 49999

    def __init__(self):
        self.rev_levels = {level: name for name, level in imm_levels.items()}

    def _post_init(self):
        self.immortals = get_all_hash('immortals')
        self.immortals.update({account: self.system_level for account in self.system_accounts})
        context.set('imm_titles', imm_levels)

    def perm_name(self, num_level):
        return self.rev_levels.get(num_level, 'player')

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

    def has_perm(self, immortal, action):
        try:
            self.check_perm(immortal, action)
            return True
        except PermError:
            return False

    def check_perm(self, immortal, action):
        if immortal.imm_level >= imm_levels['supreme']:
            return
        if isinstance(action, int):
            perm_required = action
        elif action in imm_levels:
            perm_required = imm_levels[action]
        elif hasattr(action, 'can_write'):
            if action.can_write(immortal):
                return
            raise PermError
        else:
            imm_level = getattr(action, 'imm_level', 0)
            perm_required = imm_levels.get(imm_level, imm_level)
        if immortal.imm_level < perm_required:
            raise PermError

    def perm_level(self, label):
        return imm_levels.get(label, imm_levels['admin'])

    def perm_to_level(self, label):
        return imm_levels.get(label)

    def is_supreme(self, immortal):
        return immortal.imm_level >= imm_levels['supreme']
