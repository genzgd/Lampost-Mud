from lampost.gameops.target import target_gen, recursive_targets, make_gen


@target_gen
def equip(key_type, target_key, entity, *_):
    return recursive_targets(key_type, [equip for equip in entity.inven if getattr(equip, 'current_slot', None)], target_key)
equip.absent_msg = "You don't have `{target}' equipped."


@target_gen
def inven(key_type, target_key, entity, *_):
    return recursive_targets(key_type, [equip for equip in entity.inven if not getattr(equip, 'current_slot', None)],
                             target_key)
inven.absent_msg = "You don't have `{target}'."


@target_gen
def env(key_type, target_key, entity, *_):
    for extra in entity.env.extras:
        try:
            if target_key in getattr(extra.target_keys, key_type):
                yield extra
        except AttributeError:
            pass
        for target in recursive_targets(key_type, getattr(extra, 'target_providers', ()), target_key):
            yield target


@target_gen
def feature(key_type, target_key, entity, *_):
    return recursive_targets(key_type, [feature for feature in entity.env.features], target_key)


@target_gen
def env_living(key_type, target_key, entity, *_):
    return recursive_targets(key_type, [living for living in entity.env.denizens],  target_key)


@target_gen
def env_items(key_type, target_key, entity, *_):
    return recursive_targets(key_type, [item for item in entity.env.inven], target_key)


@target_gen
def env_default(key_type, target_key, entity, *_):
    if not target_key:
        yield entity.env


@target_gen
def self_default(key_type, target_key, entity, *_):
    if not target_key:
        yield entity


make_gen('self feature env_living env_items equip inven env_default', 'default')

make_gen('self env_living self_default', 'living')

make_gen('feature env_living env_items inven equip', '__invalid__')
