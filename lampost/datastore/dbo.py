from lampost.context.resource import m_requires
from lampost.util.lmutil import cls_name

m_requires('datastore', 'encode', 'cls_registry', __name__)


class RootDBOMeta(type):
    def __new__(mcs, class_name, bases, new_attrs):
        cls = type.__new__(mcs, class_name, bases, new_attrs)
        if "RootDBO" in [base.__name__ for base in bases]:
            cls.dbo_base_class = cls
        return cls


class DBODict(dict):
    def append(self, dbo):
        self[dbo.dbo_id] = dbo

    def __iter__(self):
        return self.itervalues()

    def remove(self, dbo):
        del self[dbo.dbo_id]


class RootDBO(object):
    __metaclass__ = RootDBOMeta
    dbo_key_type = None
    dbo_set_type = None
    dbo_set_id = None
    dbo_fields = ()
    dbo_collections = ()
    dbo_refs = ()
    dbo_indexes = ()
    dbo_id = None

    def on_loaded(self):
        pass

    @property
    def dbo_key(self):
        return unicode(":".join([self.dbo_key_type, self.dbo_id]))

    @property
    def dbo_set_key(self):
        if self.dbo_set_type:
            return unicode(self.dbo_set_type + ":" + self.dbo_set_id if self.dbo_set_id else "")

    @property
    def dbo_debug_key(self):
        if self.dbo_key_type:
            return self.dbo_key
        return '-embedded-'

    @property
    def save_dbo_dict(self):
        return self._to_dbo_dict(True)

    @property
    def dbo_dict(self):
        return self._to_dbo_dict()

    @property
    def dto_value(self):
        dbo_dict = self._to_dbo_dict()
        dbo_dict['dbo_id'] = self.dbo_id
        return dbo_dict

    @property
    def json(self):
        return json_encode(self._to_dbo_dict())

    def autosave(self):
        save_object(self, autosave=True)

    def rec_describe(self, level=0, follow_refs=True):
        display = []

        def append(key, value):
            display.append(3 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp;"  + unicode(value))

        if self.dbo_id:
            append("key", self.dbo_key)
        class_name =  cls_name(self.__class__)
        base_class_name = cls_name(cls_registry(self.dbo_base_class))
        if base_class_name != class_name:
            append("class", class_name)
        if self.dbo_set_key:
            append("set_key", self.dbo_set_key)
        for field in self.dbo_fields:
            append(field, getattr(self, field, "None"))

        for ref in self.dbo_refs:
            child_dbo = getattr(self, ref.field_name, None)
            if child_dbo:
                if follow_refs or not child_dbo.dbo_key_type:
                    display.extend(child_dbo.rec_describe(level + 1))
                else:
                    append(ref.field_name, child_dbo.dbo_key)
            else:
                append(ref.field_name, "None")
        for col in self.dbo_collections:
            child_coll = getattr(self, col.field_name, None)
            if child_coll:
                append(col.field_name, "")
                for child_dbo in child_coll:
                    if follow_refs or not child_dbo.dbo_key_type:
                        display.extend(child_dbo.rec_describe(level + 1, False))
                    else:
                        append(col.field_name, child_dbo.dbo_key)
            else:
                append(col.field_name, "None")
        return display

    def _to_dbo_dict(self, use_defaults=False):
        dbo_dict = {}
        if self.__class__ != cls_registry(self.dbo_base_class):
            dbo_dict["class_name"] = self.__module__ + "." + self.__class__.__name__
        for field_name in self.dbo_fields:
            if use_defaults:
                default = getattr(self.__class__, field_name, None)
                instance = getattr(self, field_name, None)
                if instance != default:
                    dbo_dict[field_name] = getattr(self, field_name, None)
            else:
                dbo_dict[field_name] = getattr(self, field_name, None)
        for dbo_col in self.dbo_collections:
            coll_list = list()
            for child_dbo in getattr(self, dbo_col.field_name):
                if dbo_col.key_type:
                    coll_list.append(child_dbo.dbo_id)
                else:
                    coll_list.append(child_dbo._to_dbo_dict(use_defaults))
            dbo_dict[dbo_col.field_name] = coll_list
        for dbo_ref in self.dbo_refs:
            ref = getattr(self, dbo_ref.field_name, None)
            if ref:
                dbo_dict[dbo_ref.field_name] = ref.dbo_id
        return dbo_dict


class DBORef():
    def __init__(self, field_name, base_class, key_type=None):
        self.field_name = field_name
        self.base_class = base_class
        self.key_type = key_type

