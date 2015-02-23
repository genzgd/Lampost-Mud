from lampost.context.config import m_configured
from lampost.context.resource import m_requires
from lampost.util.lputil import PermError

m_requires(__name__, 'datastore')


def _on_configured():
    global _rev_levels
    _rev_levels = {level: name for name, level in imm_levels.items()}

m_configured(__name__, 'imm_levels', 'system_accounts', 'system_level')


def _post_init():
    global immortals
    immortals = get_all_hash('immortals')
    immortals.update({account: system_level for account in system_accounts})


def perm_name(num_level):
    return _rev_levels.get(num_level, 'player')


def update_immortal_list(player):
    if player.imm_level:
        set_db_hash('immortals', player.dbo_id, player.imm_level)
        immortals[player.dbo_id] = player.imm_level
    else:
        delete_index('immortals', player.dbo_id)
        try:
            del immortals[player.dbo_id]
        except KeyError:
            pass


def has_perm(immortal, action):
    try:
        check_perm(immortal, action)
        return True
    except PermError:
        return False


def check_perm(immortal, action):
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


def perm_level(label):
    return imm_levels.get(label, imm_levels['admin'])


def perm_to_level(label):
    return imm_levels.get(label)


def is_supreme(immortal):
    return immortal.imm_level >= imm_levels['supreme']
