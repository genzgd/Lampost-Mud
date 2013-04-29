import inspect
from lampost.context.resource import provides
from lampost.util.lmutil import cls_name

_registry = {}
_name_registry = {}

@provides('cls_registry')
class ClassRegistry(object):

    def __call__(self, param):
        if inspect.isclass(param):
            return _registry.get(param, param)
        return self.by_name(param)

    def set_class(self, base_cls, sub_cls):
        _registry[base_cls] = sub_cls
        _name_registry[cls_name(base_cls)] = sub_cls

    def by_name(self, full_name):
        try:
            return _name_registry[full_name]
        except KeyError:
            pass
        split_path = full_name.split(".")
        module_name = ".".join(split_path[:-1])
        cls_name = split_path[-1]
        module = __import__(module_name, globals(), locals(), [cls_name])
        cls = getattr(module, cls_name)
        _name_registry[full_name] = cls
        return cls


