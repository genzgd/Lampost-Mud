from lampost.context.resource import provides

@provides('cls_registry')
class ClassRegistry(object):
    def __init__(self):
        self.registry = {}

    def __call__(self, cls):
        return self.registry.get(cls, cls)

    def set_class(self, base_cls, sub_cls):
        self.registry[base_cls] = sub_cls

