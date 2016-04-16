from lampost.context.resource import m_requires
from lampost.datastore.classes import get_dbo_class
from lampost.datastore.exceptions import DataError
from lampost.server.handlers import MethodHandler, SessionHandler

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'perm', 'edit_notify_service')

obj_defaults = {}


class Editor(MethodHandler):
    parent_type = None
    children_types = None

    def prepare(self):
        super().prepare()
        check_perm(self.player, self)

    def initialize(self, obj_class, imm_level='builder'):
        self.obj_class = obj_class
        self.imm_level = imm_level
        self.dbo_key_type = obj_class.dbo_key_type
        if hasattr(obj_class, 'dbo_children_types'):
            self.children_types = obj_class.dbo_children_types

    def list(self):
        return [self._edit_dto(obj) for obj in load_object_set(self.obj_class) if obj.can_read(self.player)]

    def create(self):
        self.raw['owner_id'] = self.session.player.dbo_id
        self._pre_create()
        new_obj = create_object(self.obj_class, self.raw)
        self._post_create(new_obj)
        return publish_edit('create', new_obj, self.session)

    def delete_obj(self):
        del_obj = load_object(self.raw['dbo_id'], self.obj_class)
        if not del_obj:
            raise DataError('Gone: Object with key {} does not exist'.format(self.raw['dbo_id']))
        check_perm(self.player, del_obj)
        self._pre_delete(del_obj)
        holder_keys = fetch_set_keys('{}:holders'.format(del_obj.dbo_key))
        for dbo_key in holder_keys:
            cached_holder = load_cached(dbo_key)
            if cached_holder:
                save_object(cached_holder)
        delete_object(del_obj)
        for dbo_key in holder_keys:
            reloaded = reload_object(dbo_key)
            if reloaded:
                publish_edit('update', reloaded, self.session, True)
        self._post_delete(del_obj)
        publish_edit('delete', del_obj, self.session)

    def update(self):
        existing_obj = load_object(self.raw['dbo_id'], self.obj_class)
        if not existing_obj:
            raise DataError("GONE:  Object with key {} no longer exists.".format(self.raw['dbo.id']))
        check_perm(self.player, existing_obj)
        self._pre_update(existing_obj)
        if hasattr(existing_obj, 'change_owner') and self.raw['owner_id'] != existing_obj.owner_id:
            existing_obj.change_owner(self.raw['owner_id'])
        update_object(existing_obj, self.raw)
        self._post_update(existing_obj)
        return publish_edit('update', existing_obj, self.session)

    def metadata(self):
        new_object_cls = get_dbo_class(self.dbo_key_type)
        return {'perms': self._permissions(), 'parent_type': self.parent_type, 'children_types': self.children_types,
                'new_object': new_object_cls.new_dto()}

    def test_delete(self):
        return list(fetch_set_keys('{}:{}:holders'.format(self.dbo_key_type, self.raw['dbo_id'])))

    def _edit_dto(self, dbo):
        dto = dbo.edit_dto
        dto['can_write'] = dbo.can_write(self.player)
        dto['can_read'] = dbo.can_read(self.player)
        return dto

    def _pre_delete(self, del_obj):
        pass

    def _post_delete(self, del_obj):
        pass

    def _pre_create(self):
        pass

    def _post_create(self, new_obj):
        pass

    def _pre_update(self, existing_obj):
        pass

    def _post_update(self, existing_obj):
        pass

    def _permissions(self):
        return {'add': True}


class ChildList(SessionHandler):
    def initialize(self, obj_class):
        self.obj_class = obj_class
        self.dbo_key_type = obj_class.dbo_key_type
        self.parent_type = obj_class.dbo_parent_type

    def main(self, parent_id):
        parent = load_object(parent_id, self.parent_type)
        if not parent:
            self.send_error(404)
        if not parent.can_read(self.player):
            return []
        set_key = '{}_{}s:{}'.format(self.parent_type, self.dbo_key_type, parent_id)
        can_write = parent.can_write(self.player)
        child_list = []
        for child in load_object_set(self.obj_class, set_key):
            child_dto = child.edit_dto
            child_dto['can_write'] = can_write
            child_list.append(child_dto)
        self._return(child_list)


class ChildrenEditor(Editor):
    def initialize(self, obj_class, imm_level='builder'):
        super().initialize(obj_class, imm_level)
        self.parent_type = obj_class.dbo_parent_type

    def _pre_create(self):
        parent_id = self.raw['dbo_id'].split(':')[0]
        parent = load_object(parent_id, self.parent_type)
        check_perm(self.player, parent)

