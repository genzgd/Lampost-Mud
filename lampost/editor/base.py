from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import ObjectExistsError

m_requires('log', 'datastore', 'cls_registry', 'perm',  __name__)


class EditResource(Resource):

    def __init__(self, obj_class, imm_level='admin'):
        Resource.__init__(self)
        self.obj_class = cls_registry(obj_class)
        self.putChild('list', EditListResource(self, self.obj_class, imm_level))
        self.putChild('create', EditCreateResource(self, self.obj_class, imm_level))
        self.putChild('delete', EditDeleteResource(self, self.obj_class, imm_level))
        self.putChild('update', EditUpdateResource(self, self.obj_class, imm_level))

    def on_delete(self, del_obj):
        pass

    def on_create(self, new_obj):
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
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        return [load_object(self.obj_class, obj_id).dto_value for obj_id in fetch_set_keys(self.obj_class.dbo_set_key)]


class EditCreateResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        new_obj = self.obj_class(content.dbo_id)
        self.editor.on_create(new_obj)
        update_object(new_obj, content.dbo)
        new_obj.on_loaded()
        return new_obj.dto_value


class EditDeleteResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        del_obj = load_object(self.obj_class, content.dbo_id)
        delete_object(del_obj)
        self.editor.on_delete(del_obj)


class EditUpdateResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        existing_obj = load_object(self.obj_class, content.dbo['dbo_id'])
        if not existing_obj:
            raise DataError("Object with key {} no longer exists.".format(content.dbo['dbo.id']))
        update_object(existing_obj, content.dbo)
        self.editor.on_update(existing_obj)
        return existing_obj.dto_value








