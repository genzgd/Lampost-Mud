from collections import defaultdict
import logging
import sys
import inspect

log = logging.getLogger(__name__)

_registry = {}
_consumer_map = defaultdict(list)
_methods = {}
_registered_modules = []


def register(name, service, export_methods=False):
    _registry[name] = service
    if service not in _registered_modules:
        _registered_modules.append(service)
    if export_methods:
        _methods[name] = {}
        if inspect.ismodule(service):
            for attr, value in service.__dict__.items():
                if not attr.startswith("_") and not _registry.get(attr) and hasattr(value, '__call__'):
                    _methods[name][attr] = value
        else:
            for attr, value in service.__class__.__dict__.items():
                if not attr.startswith("_") and not _registry.get(attr) and hasattr(value, '__call__'):
                    _methods[name][attr] = value.__get__(service, service.__class__)
    for cls in _consumer_map.get(name, []):
        _inject(cls, name, service)
    if name in _consumer_map:
        del _consumer_map[name]
    return service


def inject(cls, name):
    service = _registry.get(name, None)
    if service:
        _inject(cls, name, service)
        return
    _consumer_map[name].append(cls)


def requires(*resources):
    def wrapper(cls):
        for name in resources:
            inject(cls, name)
        return cls
    return wrapper


def m_requires(module_name, *resources):
    module = sys.modules[module_name]
    for name in resources:
        inject(module, name)
    if module not in _registered_modules:
        _registered_modules.append(module)


def get_resource(name):
    return _registry[name]


def context_post_init():
    for name, consumers in _consumer_map.items():
        for consumer in consumers:
            log.error("{} dependency not found for consumer {}", name, getattr(consumer, '__name__', consumer))
    for module in sorted(_registered_modules, key=_priority_sort):
        if hasattr(module, '_post_init'):
            module._post_init()


def _priority_sort(module):
    try:
        return getattr(module, '_init_priority')
    except AttributeError:
        if inspect.isclass(module):
            return 1000
        return 2000


def _inject(cls, name, service):
    if hasattr(service, 'factory'):
        setattr(cls, name, service.factory(cls))
    else:
        setattr(cls, name, service)
    for attr, value in _methods.get(name, {}).items():
        if not getattr(cls, attr, None):
            setattr(cls, attr, value)
