def recursive_targets(target_list, target_key):
    for target in target_list:
        if target_key in getattr(target, 'target_keys', ()):
            yield target
        for target in recursive_targets(getattr(target, 'target_providers', ()), target_key):
            yield target

def self(entity, target_key, *_):
    if target_key == ('self',) or target_key in entity.target_keys:
        yield entity


def func_owner(target_key, func, *_):
    return recursive_targets([func.__self__], target_key)


def action(entity, target_key, action):
    return recursive_targets([action], target_key)


def equip(entity, target_key, *_):
    return recursive_targets([equip for equip in entity.inven if equip.current_slot], target_key)
equip.absent_msg = "You don't have `{target}' equipped"


def inven(entity, target_key, *_):
    return recursive_targets([equip for equip in entity.inven if not equip.current_slot], target_key)
inven.absent_msg = "You don't have `{target}'"


def env(entity, target_key, *_):
    if not target_key:
        yield entity.env
    for extra in entity.env.extras:
        if target_key in getattr(extra, 'target_keys', ()):
            yield extra
        for target in recursive_targets(getattr(extra, 'target_providers', ()), target_key):
            yield target


def feature(entity, target_key, *_):
    return recursive_targets([feature for feature in entity.env.features], target_key)


def env_living(entity, target_key, *_):
    return recursive_targets([living for living in entity.env.denizens],  target_key)


def env_items(entity, target_key, *_):
    return recursive_targets([item for item in entity.env.inven], target_key)


defaults = [self, equip, inven, env, feature, env_living, env_items]

def make(target_class):
    try:
        return [globals()[t_class] for t_class in target_class.split(' ')]
    except (AttributeError, KeyError):
        return target_class
