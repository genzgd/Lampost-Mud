class TargetClass(object):
    def __init__(self, target_finder, absent_msg="{target is not here}"):
        self.target_finder = target_finder.__get__(self)
        self.absent_msg = absent_msg


def recursive_targets(target_list, target_key):
    for target in target_list:
        if target_key in getattr(target, 'target_keys', ()):
            yield target
        for target in recursive_targets(getattr(target, 'target_providers', ()), target_key):
            yield target


def self_finder(self, entity, target_key):
    if target_key == ('self',) or target_key in entity.target_keys:
        yield entity


def equip_finder(self, entity, target_key):
    return recursive_targets([equip for equip in entity.inven if equip.current_slot], target_key)


def inven_finder(self, entity, target_key):
    return recursive_targets([equip for equip in entity.inven if not equip.current_slot], target_key)


def env_finder(self, entity, target_key):
    if not target_key:
        yield entity.env


def feature_finder(self, entity, target_key):
    return recursive_targets([feature for feature in entity.env.features], target_key)


def env_living_finder(self, entity, target_key):
    return recursive_targets([living for living in entity.env.contents if getattr(living, 'living', None)], target_key)


def env_items_finder(self, entity, target_key):
    return recursive_targets([item for item in entity.env.contents if not getattr(item, 'living', None)], target_key)


TargetClass.NONE = TargetClass(lambda self, entity, target_key: ())
TargetClass.SELF = TargetClass(self_finder)
TargetClass.EQUIP = TargetClass(equip_finder)
TargetClass.INVEN = TargetClass(inven_finder)
TargetClass.ENV = TargetClass(env_finder)
TargetClass.FEATURE = TargetClass(feature_finder)
TargetClass.ENV_LIVING  = TargetClass(env_living_finder)
TargetClass.ENV_ITEMS = TargetClass(env_items_finder)

TargetClass.DEFAULTS = [TargetClass.SELF, TargetClass.EQUIP, TargetClass.EQUIP, TargetClass.INVEN, TargetClass.ENV, TargetClass.FEATURE,
                        TargetClass.ENV_LIVING, TargetClass.ENV_ITEMS]
