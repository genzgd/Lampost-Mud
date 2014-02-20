from lampost.context.resource import m_requires
from lampost.editor.areas import AreaListResource, parent_area
from lampost.editor.base import EditResource
from lampost.gameops.script import Script


m_requires('perm', __name__)


class ScriptResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Script)
        self.putChild('list', AreaListResource(Script))

    def pre_create(self, dto, session):
        check_perm(session, parent_area(dto))

    def pre_update(self, dbo, session):
        check_perm(session, parent_area(dbo))

    def pre_delete(self, dbo, session):
        check_perm(session, parent_area(dbo))
