from twisted.web.resource import Resource
from lampost.client.handlers import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError

m_requires('log', 'datastore', 'perm', 'edit_update_service',  __name__)


class EditResource(Resource):
    def __init__(self, obj_class, imm_level='admin'):
        Resource.__init__(self)
        self.obj_class = obj_class
        self.imm_level = imm_level
        self.putChild('list', EditListResource(self))
        self.putChild('create', EditCreateResource(self))
        self.putChild('delete', EditDeleteResource(self))
        self.putChild('update', EditUpdateResource(self))
        self.putChild('test_delete', EditTestDeleteResource(self))

    def pre_delete(self, del_obj, session):
        pass

    def post_delete(self, del_obj, session):
        pass

    def pre_create(self, obj_dict, session):
        pass

    def post_create(self, new_obj, session):
        pass

    def pre_update(self, existing_obj, new_dto, session):
        pass

    def post_update(self, existing_obj, session):
        pass


class EditBaseResource(Resource):
    def __init__(self, editor):
        Resource.__init__(self)
        self.editor = editor
        self.obj_class = editor.obj_class
        self.dbo_key_type = self.obj_class.dbo_key_type
        self.imm_level = editor.imm_level


class EditListResource(EditBaseResource):
    @request
    def render_POST(self, session):
        return [edit_dto(session.player, obj) for obj in load_object_set(self.obj_class)]


class EditCreateResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        raw['owner_id'] = session.player.dbo_id
        self.editor.pre_create(raw, session)
        new_obj = create_object(self.obj_class, raw)
        self.editor.post_create(new_obj, session)
        return publish_edit('create', new_obj, session)


class EditDeleteResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        del_obj = load_object(self.obj_class, raw['dbo_id'])
        if not del_obj:
            raise DataError('Gone: Object with key {} does not exist'.format(raw['dbo_id']))
        check_perm(session, del_obj)
        self.editor.pre_delete(del_obj, session)
        holder_keys = fetch_holders(self.dbo_key_type, del_obj.dbo_id)
        for key_type, dbo_id in holder_keys:
            cached_holder = load_cached(key_type, dbo_id)
            if cached_holder:
                save_object(cached_holder)
        delete_object(del_obj)
        for key_type, dbo_id in holder_keys:
            reloaded = reload_object(key_type, dbo_id)
            if reloaded:
                publish_edit('update', reloaded, session, True)
        self.editor.post_delete(del_obj, session)
        publish_edit('delete', del_obj, session)


class EditUpdateResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        existing_obj = load_object(self.obj_class, raw['dbo_id'])
        if not existing_obj:
            raise DataError("GONE:  Object with key {} no longer exists.".format(raw['dbo.id']))
        check_perm(session, existing_obj)
        self.editor.pre_update(existing_obj, raw, session)
        update_object(existing_obj, raw)
        self.editor.post_update(existing_obj, session)
        return publish_edit('update', existing_obj, session)


class EditTestDeleteResource(EditBaseResource):
    @request
    def render_POST(self, raw):
        return ['{} - {}'.format(key_type, dbo_id) for key_type, dbo_id in fetch_holders(self.dbo_key_type, raw['dbo_id'])]
