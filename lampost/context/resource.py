def _inject(cls, name, service):
    setattr(cls, name, service)
    for attr, value in _methods.get(name, {}).iteritems():
        if not getattr(cls, attr, None):
            setattr(cls, attr, value)

def register(name, service):
    _registry[name] = service
    _methods[name] = {}
    for attr, value in service.__class__.__dict__.iteritems():
        if not attr.startswith("_") and hasattr(value, '__call__'):
            _methods[name][attr] = value.__get__(service, service.__class__)
    for cls in _consumers.get(name, []):
        _inject(cls, name, service)
    if _consumers.get(name, None):
        del _consumers[name]

def inject(cls, name):
    service = _registry.get(name, None)
    if service:
        _inject(cls, name, service)
        return
    _consumers[name] = _consumers.get(name, [])
    _consumers[name].append(cls)

def provides(name):
    def wrapper(cls):
        original_init = cls.__init__
        def init_and_register(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            register(name, self)
        cls.__init__ = init_and_register
        return cls
    return wrapper

def requires(*resources):
    def wrapper(cls):
        for name in resources:
            inject(cls, name)
        return cls
    return wrapper

_registry = {}
_consumers = {}
_methods = {}