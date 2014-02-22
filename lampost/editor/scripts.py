from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
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

    def pre_update(self, dbo, new_dto, session):
        check_perm(session, parent_area(dbo))
        try:
            compile(new_dto['text'], '<string>', 'exec')
        except SyntaxError as syn_error:
            raise DataError("Syntax Error: {}  text:{}  line: {}  offset: {}".format(syn_error.msg, syn_error.text, syn_error.lineno, syn_error.offset))
        except BaseException as other_error:
            raise DataError("Script Error: {}".format(other_error.msg))
        new_dto['approved'] = has_perm(session, 'admin')

    def pre_delete(self, dbo, session):
        check_perm(session, parent_area(dbo))
