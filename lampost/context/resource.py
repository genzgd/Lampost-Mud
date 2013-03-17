import sys


def register(name, service, export_methods=False):
    _registry[name] = service
    _registered_services.append(service)
    if export_methods:
        _methods[name] = {}
        for attr, value in service.__class__.__dict__.iteritems():
            if not attr.startswith("_") and not _registry.get(attr) and hasattr(value, '__call__'):
                _methods[name][attr] = value.__get__(service, service.__class__)
    for cls in _consumer_map.get(name, []):
        _inject(cls, name, service)
    if _consumer_map.get(name, None):
        del _consumer_map[name]


def inject(cls, name):
    service = _registry.get(name, None)
    if service:
        _inject(cls, name, service)
        return
    _consumer_map[name] = _consumer_map.get(name, [])
    _consumer_map[name].append(cls)


def provides(name, export_methods=False):
    def wrapper(cls):
        original_init = cls.__init__

        def init_and_register(self, *args, **kwargs):
            register(name, self, export_methods)
            original_init(self, *args, **kwargs)

        cls.__init__ = init_and_register
        return cls
    return wrapper


def requires(*resources):
    def wrapper(cls):
        for name in resources:
            inject(cls, name)
        return cls
    return wrapper


def m_requires(*resources):
    module = sys.modules[resources[-1]]
    for name in resources[:-1]:
        inject(module, name)
    _registered_modules.append(module)


def get_resource(name):
    return _registry[name]


def context_post_init():
    for module in _registered_modules:
        try:
            module._post_init()
        except AttributeError:
            pass
    for service in _registered_services:
        try:
            service._post_init()
        except AttributeError:
            pass


def _inject(cls, name, service):
    setattr(cls, name, service)
    for attr, value in _methods.get(name, {}).iteritems():
        if not getattr(cls, attr, None):
            setattr(cls, attr, value)


_registry = {}
_consumer_map = {}
_methods = {}
_registered_modules = []
_registered_services = []