from lampost.datastore.classes import get_dbo_class, set_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.dbofield import DBOField, value_wrapper
from lampost.datastore.meta import CommonMeta, call_mro

m_requires(__name__, 'log', 'perm', 'datastore')


class CoreDBO(metaclass=CommonMeta):
    dbo_owner = None
    template_id = None

    def _on_loaded(self):
        for load_func in self.load_funcs:
            load_func(self)

    def hydrate(self, dto):
        for field, dbo_field in self.dbo_fields.items():
            if field in dto:
                dbo_value = dbo_field.hydrate_value(dto[field], self)
                setattr(self, field, dbo_value)
            else:
                dbo_value = None
                try:
                    delattr(self, field)
                except AttributeError:
                    pass
            if not dbo_value and dbo_field.required:
                warn("Missing required field {} in object {}", field, dto)
                return None
        self._on_loaded()
        return self

    def clone(self):
        clone = self.__class__(getattr(self, 'dbo_id', None))
        clone.template = self
        clone._on_loaded()
        return clone

    @property
    def save_value(self):
        save_value = {}
        for field, dbo_field in self.dbo_fields.items():
            try:
                save_value[field] = dbo_field.save_value(self)
            except KeyError:
                continue
        return self.metafields(save_value, ['template_key'])

    def describe(self):
        return self._describe([], 0)

    @property
    def dto_value(self):
        return {field: dbo_field.dto_value(getattr(self, field)) for field, dbo_field in self.dbo_fields.items()}

    @property
    def edit_dto(self):
        return self.metafields(self.dto_value, ['class_id'])

    def metafields(self, dto_repr, field_names):
        for metafield in field_names:
            try:
                dto_repr[metafield] = getattr(self, metafield)
            except AttributeError:
                pass
        return dto_repr

    def _describe(self, display, level):
        if level > 2:
            return

        def append(value, key):
            display.append(4 * level * "&nbsp;" + key + ":" + (16 - len(key)) * "&nbsp;" + str(value))

        for attr in ['class_id', 'dbo_key_type', 'dbo_id', 'template_key']:
            if hasattr(self, attr):
                append(getattr(self, attr), attr)
        for field, dbo_field in sorted(self.dbo_fields.items(), key=lambda field_value: field_value[0]):
            value = getattr(self, field)
            try:
                dbo_field.check_default(value)
                wrapper = value_wrapper(value)
                if hasattr(dbo_field, 'dbo_class_id'):
                    append('', field)
                    wrapper(lambda value: value._describe(display, level + 1))(value)
                else:
                    wrapper(append)(value, field)
            except KeyError:
                pass

        return display

    def can_read(self, immortal):
        return True

    def can_write(self, immortal):
        return is_supreme(immortal) or immortal.imm_level > getattr(self, 'imm_level', 0)


class DBOAccess(metaclass=CommonMeta):
    owner_id = DBOField('lampost')
    read_access = DBOField(0)
    write_access = DBOField(0)

    @property
    def imm_level(self):
        try:
            return perm.immortals[self.owner_id] + 1
        except KeyError:
            return perm_to_level('admin')

    def can_read(self, immortal):
        return immortal.imm_level >= self.read_access

    def can_write(self, immortal):
        if is_supreme(immortal) or immortal.dbo_id == self.owner_id:
            return True
        if self.write_access:
            return immortal.imm_level >= self.write_access
        return immortal.imm_level >= self.imm_level

    def on_created(self):
        info("{} created new object {}", self.owner_id, self.dbo_key)
        add_set_key('owned:{}'.format(self.owner_id), self.dbo_key)

    def on_deleted(self):
        delete_set_key('owned:{}'.format(self.owner_id), self.dbo_key)

    def change_owner(self, new_owner=None):
        self.on_deleted()
        self.owner_id = new_owner or 'lampost'
        self.on_created()


class KeyDBO(CoreDBO):
    dbo_key_sort = None
    dbo_indexes = ()
    dbo_children_types = ()

    dbo_rev = DBOField(0)

    @property
    def dbo_key(self):
        return ":".join([self.dbo_key_type, self.dbo_id])

    @property
    def edit_dto(self):
        return self.metafields(self.dto_value, ['dbo_id', 'dbo_key', 'class_id',  'dbo_key_type', 'imm_level'])

    @property
    def new_dto(self):
        dto = self.dto_value
        dto['can_write'] = True
        return self.metafields(dto, ['class_id', 'dbo_key_type', 'dbo_parent_type', 'dbo_children_types'])

    def db_created(self):
        call_mro(self, 'on_created')

    def db_deleted(self):
        call_mro(self, 'on_deleted')

    def autosave(self):
        save_object(self, autosave=True)


class ParentDBO(DBOAccess, KeyDBO):

    @property
    def edit_dto(self):
        dto = self.dto_value
        for child_type in self.dbo_children_types:
            dto['{}_list'.format(child_type)] = self.dbo_child_keys(child_type)
        return self.metafields(dto, ['dbo_id', 'dbo_key', 'class_id', 'dbo_key_type', 'dbo_children_types'])

    def dbo_child_keys(self, child_type):
        child_class = get_dbo_class(child_type)
        return sorted(fetch_set_keys("{}_{}s:{}".format(self.dbo_key_type, child_type, self.dbo_id)),
                      key=child_class.dbo_key_sort)


class ChildDBO(KeyDBO):

    @property
    def parent_id(self):
        return self.dbo_id.split(':')[0]

    @property
    def parent_dbo(self):
        return load_object(self.parent_id, self.dbo_parent_type)

    @property
    def dbo_set_key(self):
        return "{}_{}s:{}".format(self.dbo_parent_type, self.dbo_key_type, self.parent_id)

    @property
    def edit_dto(self):
        return self.metafields(self.dto_value, ['dbo_id', 'dbo_key', 'class_id',  'dbo_key_type', 'dbo_parent_type'])

    @property
    def imm_level(self):
        return self.parent_dbo.imm_level

    def can_read(self, immortal):
        return self.parent_dbo.can_read(immortal)

    def can_write(self, immortal):
        return self.parent_dbo.can_write(immortal)


class Untyped():
    def hydrate(self, dto_repr):
        # This should never get called, as 'untyped' fields should always hold
        # templates or actual dbo_references with saved class_ids
        warn("Attempting to hydrate invalid dto {}", dto_repr)


set_dbo_class('untyped', Untyped)
