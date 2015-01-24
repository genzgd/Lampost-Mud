from lampost.util.lputil import tuples_to_list


ATTRIBUTES = tuples_to_list(('dbo_id', 'name', 'category', 'hidden'), [
    ('con', 'Constitution', 'Brawn', False),
    ('str', 'Strength', 'Brawn', False),
    ('agi', 'Agility', 'Brawn', False),
    ('adv', 'Adventuresome', 'Brawn', True),
    ('int', 'Intelligence', 'Brain', False),
    ('wis', 'Wisdom', 'Brain', False),
    ('kno', 'Knowledge', 'Brain', False),
    ('cur', 'Curiosity', 'Brain', True),
    ('cha', 'Charm', 'Bravado', False),
    ('bal', 'Balance', 'Bravado', False),
    ('gui', 'Guile', 'Bravado', False),
    ('inq', 'Inquiry', 'Bravado', True)
])

ATTR_LIST = tuple([attr['dbo_id'] for attr in ATTRIBUTES])

RESOURCE_POOLS = tuples_to_list(('dbo_id', 'name', 'desc', 'calc'), [
    ('health', 'Health', 'Physical well being resource', [['con', 11], ['str', 3], ['adv', 1], ['agi', 1]]),
    ('mental', 'Mana', 'Mental energy resource', [['int', 7], ['wis', 5], ['kno', 2], ['cur', 2]]),
    ('stamina', 'Stamina', 'Physical energy resource', [['con', 10], ['str', 2], ['wis', 2], ['bal', 2]]),
    ('action', 'Action', 'Action points pool', [['con', 5], ['bal', 5], ['wis', 3], ['agi', 2]])

])

POOL_KEYS = tuple([(pool['dbo_id'], 'base_{}'.format(pool['dbo_id'])) for pool in RESOURCE_POOLS])


def base_pools(entity):
    for pool in RESOURCE_POOLS:
        calc = pool['calc']
        total = sum(getattr(entity, calc[0]) * calc[1] for calc in calc)
        setattr(entity, 'base_{}'.format(pool['dbo_id']), total)


def fill_pools(entity):
    base_pools(entity)
    for pool_id, base_pool_id in POOL_KEYS:
        setattr(entity, pool_id, getattr(entity, base_pool_id))


def restore_attrs(entity):
    for attr in ATTR_LIST:
        setattr(entity, attr, getattr(entity, "perm_{}".format(attr)))


def need_refresh(entity):
    for pool_id, base_pool_id in POOL_KEYS:
        if getattr(entity, pool_id) < getattr(entity, base_pool_id):
            return True

