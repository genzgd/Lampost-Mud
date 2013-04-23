from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import ObjectExistsError

m_requires('log', 'datastore', 'cls_registry', 'perm',  __name__)


class EditResource(Resource):

    def __init__(self, obj_class, imm_level='admin'):
        Resource.__init__(self)
        self.obj_class = cls_registry(obj_class)
        self.putChild('list', EditListResource(obj_class, imm_level))
        self.putChild('create', EditCreateResource(obj_class, imm_level))
        self.putChild('delete', EditDeleteResource(obj_class, imm_level))
        self.putChild('update', EditUpdateResource(obj_class, imm_level))


class EditBaseResource(Resource):
    def __init__(self, obj_class, imm_level):
        Resource.__init__(self)
        self.obj_class = obj_class
        self.imm_level = imm_level


class EditListResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        return [load_object(self.obj_class, obj_id).dto_value for obj_id in fetch_set_keys(self.obj_class.dbo_set_key)]


class EditCreateResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        if object_exists(self.obj_class.dbo_key_type, content.dbo_id):
            raise ObjectExistsError(content.dbo_id)
        new_obj = self.obj_class(content.dbo_id)
        update_object(new_obj, content.dbo)
        return new_obj.dto_value


class EditDeleteResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        delete_object(load_object(self.obj_class, content.dbo_id))


class EditUpdateResource(EditBaseResource):

    @request
    def render_POST(self, content, session):
        check_perm(session, self.imm_level)
        existing = load_object(self.obj_class, content.dbo['dbo_id'])
        if not existing:
            raise DataError("Object with key {} no longer exists.".format(content.dbo['dbo.id']))
        update_object(existing, content.dbo)
        return existing.dto_value








