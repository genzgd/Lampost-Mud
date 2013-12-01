from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import ObjectExistsError

m_requires('log', 'datastore', 'cls_registry', 'perm',  __name__)


class EditResource(Resource):

    def __init__(self, obj_class, imm_level='admin'):
        Resource.__init__(self)
        self.putChild('list', EditListResource(self, obj_class, imm_level))
        self.putChild('create', EditCreateResource(self, obj_class, imm_level))
        self.putChild('delete', EditDeleteResource(self, obj_class, imm_level))
        self.putChild('update', EditUpdateResource(self, obj_class, imm_level))

    def pre_delete(self, del_obj):
        pass

    def on_delete(self, del_obj):
        pass

    def pre_create(self, obj_dict):
        pass

    def on_create(self, new_obj):
        pass

    def pre_update(self, obj_dict):
        pass

    def on_update(self, existing_obj):
        pass


class EditBaseResource(Resource):
    def __init__(self, editor, obj_class, imm_level):
        Resource.__init__(self)
        self.obj_class = obj_class
        self.imm_level = imm_level
        self.editor = editor


class EditListResource(EditBaseResource):
    @request
    def render_POST(self, session):
        check_perm(session, self.imm_level)
        return [load_object(self.obj_class, obj_id).dto_value for obj_id in fetch_set_keys(self.obj_class.dbo_set_key)]


class EditCreateResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        raw['owner_id'] = session.player.dbo_id
        self.editor.pre_create(raw)
        new_obj = create_object(self.obj_class, raw)
        self.editor.on_create(new_obj)
        return new_obj.dto_value


class EditDeleteResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        del_obj = load_object(self.obj_class, raw['dbo_id'])
        if not del_obj:
            raise DataError('Gone: Object with key {} does not exist'.format(content.dbo_id))
        check_perm(session, del_obj)
        self.editor.pre_delete(del_obj)
        delete_object(del_obj)
        self.editor.on_delete(del_obj)


class EditUpdateResource(EditBaseResource):
    @request
    def render_POST(self, raw, session):
        self.editor.pre_update(raw)
        existing_obj = load_object(self.obj_class, raw['dbo_id'])
        if not existing_obj:
            raise DataError("Gone: Object with key {} no longer exists.".format(raw['dbo.id']))
        check_perm(session, existing_obj)
        update_object(existing_obj, raw)
        self.editor.on_update(existing_obj)
        return existing_obj.dto_value
