def cls_name(cls):
    return ".".join([cls.__module__, cls.__name__])


def subclasses(cls):
    yield cls
    for subclass in cls.__subclasses__():
        yield subclass
        for sub_sub in subclasses(subclass):
            yield sub_sub
