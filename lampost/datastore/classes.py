import logging
import inspect
import itertools


_dbo_registry = {}
_mixin_registry = {}
_mixed_registry = {}

log = logging.getLogger(__name__)


def check_dbo_class(class_id):
    return _dbo_registry.get(class_id)


def set_dbo_class(class_id, dbo_class):
    if isinstance(class_id, str):
        old_class = check_dbo_class(class_id)
        if old_class:
            log.info("Overriding {} with {} as {}", cls_name(old_class), cls_name(dbo_class), class_id)
        else:
            log.debug("Registering {} as {}", cls_name(dbo_class), class_id)
        _dbo_registry[class_id] = dbo_class

    else:
        log.warn("Attempting to register invalid class_id {}", class_id)


def set_mixin(class_id, mixin_class):
    _mixin_registry[class_id] = mixin_class


def get_dbo_class(class_id):
    try:
        return _dbo_registry[class_id]
    except KeyError:
        log.exception("No class found in registry for dbo class id: {}", class_id)


def get_mixed_type(class_id, mixins):
    main_class = get_dbo_class(class_id)
    if not mixins:
        return main_class
    mixin_key = frozenset(itertools.chain(mixins, (class_id,)))
    try:
        return _mixed_registry[mixin_key]
    except KeyError:
        mixin_bases = (main_class,) + tuple(_mixin_registry[mixin] for mixin in mixins)
        mixin_class = type("_".join(mixin_key), mixin_bases, {'mixins': mixins})
        _mixed_registry[mixin_key] = mixin_class
        return mixin_class


def cls_name(cls):
    return ".".join([cls.__module__, cls.__name__])


def subclasses(cls):
    yield cls
    for subclass in cls.__subclasses__():
        yield subclass
        for sub_sub in subclasses(subclass):
            yield sub_sub


def dbo_types(cls):
    return {subclass for subclass in subclasses(cls) if hasattr(subclass, 'dbo_key_type')}


def implementors(base_class):
    for key, value in _dbo_registry.items():
        if base_class != value and base_class in inspect.getmro(value):
            yield key

