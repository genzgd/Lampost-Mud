ATTR_MAP = {'con': {'name': 'Constitution', 'category': 'Brawn', 'hidden': False},
            'str': {'name': 'Strength', 'category': 'Brawn', 'hidden': False},
            'agi': {'name': 'Agility', 'category': 'Brawn', 'hidden': False},
            'adv': {'name': 'Adventuresome', 'category': 'Brawn', 'hidden': True},

            'int': {'name': 'Intelligence', 'category': 'Brain', 'hidden': False},
            'wis': {'name': 'Wisdom', 'category': 'Brain', 'hidden': False},
            'kno': {'name': 'Knowledge', 'category': 'Brain', 'hidden': False},
            'cur': {'name': 'Curiosity', 'category': 'Brain', 'hidden': True},

            'cha': {'name': 'Charm', 'category': 'Bravado', 'hidden': False},
            'bal': {'name': 'Balance', 'category': 'Bravado', 'hidden': False},
            'gui': {'name': 'Guile', 'category': 'Bravado', 'hidden': False},
            'inq': {'name': 'Inquiry', 'category': 'Bravado', 'hidden': True}}

ATTR_LIST = tuple(ATTR_MAP.iterkeys())


POOL_MAP = {'health': {'name': 'Health', 'desc': 'Physical well being resource',
                       'calc': [['con', 11],['str', 3], ['adv', 1], ['agi', 1]]},
            'mental': {'name': 'Mana', 'desc': 'Mental energy resource',
                       'calc': [['int', 7],['wis', 5], ['kno', 2], ['cur', 2]]},
            'stamina': {'name': 'Stamina', 'desc': 'Physical energy resource',
                        'calc': [['con', 10],['str', 2], ['wis', 2], ['bal', 2]]},
            'action': {'name': 'Action', 'desc': 'Action points pool',
                       'calc': [['con', 5],['bal', 5], ['wis', 3], ['agi', 2]]}}

POOL_LIST = tuple(POOL_MAP.iterkeys())


def calc_pools(entity):
    for pool_id, value in POOL_MAP.iteritems():
        total = sum(getattr(entity, calc[0]) * calc[1] for calc in value['calc'])
        setattr(entity, pool_id, total)


def restore_attrs(entity):
    for attr in ATTR_LIST:
        setattr(entity, attr, getattr(entity, "perm_{}".format(attr)))

