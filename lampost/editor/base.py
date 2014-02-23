from twisted.web.resource import Resource
from lampost.client.resources import request
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
        self.imm_level = editor.imm_level

    @property
    def cache_key(self):
        return self.obj_class.dbo_key_type


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
        delete_object(del_obj)
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
        mobile = load_object(self.obj_class, raw['dbo_id'])
        if not mobile:
            raise DataError("GONE:  Object already deleted")
        return list(fetch_set_keys(mobile.reset_key))
