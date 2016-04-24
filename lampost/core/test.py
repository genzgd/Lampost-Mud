class CoreMeta(type):

    def __init__(cls, name, bases, new_attrs):
        cls._extend(bases, "_cls_inits", "_cls_init")
        for cls_init in cls._cls_inits:
            cls_init(cls, name, bases, new_attrs)
        mixin_init = new_attrs.get("_mixin_init")
        if mixin_init:
            cls._cls_inits.append(getattr(mixin_init, "__func__", mixin_init))

    def _extend(cls, bases, cls_field, attr_name):
        new_field = []
        for base in bases:
            new_field.extend(getattr(base, cls_field, []))
        new_attr = getattr(cls, attr_name, None)
        if new_attr:
            new_field.append(getattr(new_attr, "__func__", new_attr))
        setattr(cls, cls_field, new_field)

    def _update(cls, bases, attr_name):
        new_field = {}
        for base in bases:
            new_field.update({key: value for key, value in getattr(base, attr_name, {}).items()})
        setattr(cls, attr_name, new_field)

    def _update_set(cls, bases, attr_name):
        new_field = set()
        for base in bases:
            new_field.update(getattr(cls, attr_name, set()))
        setattr(cls, attr_name, new_field)