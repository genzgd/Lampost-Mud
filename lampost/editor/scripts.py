from lampost.datastore.exceptions import DataError
from lampost.editor.children import EditChildrenResource


class ScriptResource(EditChildrenResource):

    def pre_update(self, dbo, new_dto, session):
        self._check_perm(dbo, session)
        try:
            compile(new_dto['text'], '<string>', 'exec')
        except SyntaxError as syn_error:
            raise DataError("Syntax Error: {}  text:{}  line: {}  offset: {}".format(syn_error.msg, syn_error.text, syn_error.lineno, syn_error.offset))
        except BaseException as other_error:
            raise DataError("Script Error: {}".format(other_error.msg))
        new_dto['approved'] = has_perm(session, 'admin')

