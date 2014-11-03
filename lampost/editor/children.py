from twisted.web.resource import Resource
from lampost.client.handlers import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource, EditBaseResource

m_requires('perm', 'datastore', __name__)


class EditChildrenResource(EditResource):
    def __init__(self, obj_class, imm_level='admin'):
        EditResource.__init__(self, obj_class, imm_level)
        self.parent_type = obj_class.dbo_parent_type
        self.putChild('list', ChildrenListResource(self))

    def _check_perm(self, obj, session):
        check_perm(session, find_parent(obj, self.parent_type))

    def pre_delete(self, del_obj, session):
        self._check_perm(del_obj, session)

    def pre_create(self, obj_dict, session):
        self._check_perm(obj_dict, session)

    def pre_update(self, existing_obj, new_dto, session):
        self._check_perm(existing_obj, session)


class ChildrenListResource(EditBaseResource):
    def __init__(self, editor):
        EditBaseResource.__init__(self, editor)

    def getChild(self, parent_id, request):
        return ChildrenListLeaf(self.editor, parent_id)


class ChildrenListLeaf(Resource):
    def __init__(self, editor, parent_id):
        Resource.__init__(self)
        self.parent_type = editor.parent_type
        self.obj_class = editor.obj_class
        self.imm_level = editor.imm_level
        self.parent_id = parent_id

    @request
    def render_POST(self):
        set_key = '{}_{}s:{}'.format(self.parent_type, self.obj_class.dbo_key_type, self.parent_id)
        return [obj.dto_value for obj in load_object_set(self.obj_class, set_key)]


def find_parent(child, parent_type=None):
    try:
        dbo_id = child.dbo_id
        parent_type = child.dbo_parent_type
    except AttributeError:
        dbo_id = child['dbo_id']
    parent = load_by_key(parent_type, dbo_id.split(':')[0])
    if not parent:
        raise DataError("Parent Missing")
    return parent

