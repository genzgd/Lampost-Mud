import inspect
from lampost.context.resource import provides, m_requires
from lampost.util.lmutil import cls_name

m_requires('log', __name__)

_registry = {None: None}
_dbo_registry = {None: None}

@provides('cls_registry')
class ClassRegistry(object):
    def __call__(self, param):
        try:
            return _registry[param]
        except KeyError:
            if inspect.isclass(param):
                self.set_class(param, param)
                return param
            warn("Cannot find key type for {}".format(param), self)

    def set_class(self, base_cls, sub_cls):
        _registry[base_cls] = sub_cls
        try:
            _registry[base_cls.dbo_key_type] = sub_cls
        except AttributeError:
            pass

    def set_dbo_class(self, class_id, dbo_class):
        _dbo_registry[class_id] = dbo_class

