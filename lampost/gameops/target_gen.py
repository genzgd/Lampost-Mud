from lampost.context.resource import m_requires

m_requires(__name__, 'session_manager')


def recursive_targets(target_list, target_key):
    for target in target_list:
        if target_key in getattr(target, 'target_keys', ()):
            yield target
        for sub_target in recursive_targets(getattr(target, 'target_providers', ()), target_key):
            yield sub_target


def self(target_key, entity, *_):
    if target_key == ('self',) or target_key in entity.target_keys:
        yield entity


def func_owner(target_key, entity, action, *_):
    return recursive_targets([action.__self__], target_key)


def func_providers(target_key, entity, action, *_):
    for target in action.__self__.target_providers:
        if target_key in getattr(target, 'target_keys', ()):
            yield target


def action(target_key, entity, action):
    return recursive_targets([action], target_key)


def equip(target_key, entity, *_):
    return recursive_targets([equip for equip in entity.inven if getattr(equip, 'current_slot', None)], target_key)
equip.absent_msg = "You don't have `{target}' equipped."


def inven(target_key, entity, *_):
    return recursive_targets([equip for equip in entity.inven if not getattr(equip, 'current_slot', None)], target_key)
inven.absent_msg = "You don't have `{target}'."


def env(target_key, entity, *_):
    if not target_key:
        yield entity.env
    for extra in entity.env.extras:
        if target_key in getattr(extra, 'target_keys', ()):
            yield extra
        for target in recursive_targets(getattr(extra, 'target_providers', ()), target_key):
            yield target


def feature(target_key, entity, *_):
    return recursive_targets([feature for feature in entity.env.features], target_key)


def env_living(target_key, entity, *_):
    return recursive_targets([living for living in entity.env.denizens],  target_key)


def env_items(target_key, entity, *_):
    return recursive_targets([item for item in entity.env.inven], target_key)


defaults = [self, equip, inven, env, feature, env_living, env_items]


def logged_in(target_key, *_):
    session = session_manager.player_session(" ".join(target_key))
    if session:
        yield session.player
logged_in.absent_msg = "That player is not logged in."


def make(target_class):
    try:
        return [globals()[t_class] for t_class in target_class.split(' ')]
    except (AttributeError, KeyError):
        if hasattr(target_class, '__iter__'):
            return target_class
        return [target_class]
