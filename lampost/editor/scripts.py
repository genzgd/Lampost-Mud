from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.children import EditChildrenResource

m_requires('perm', 'script_manager', __name__)


class ScriptResource(EditChildrenResource):

    def pre_update(self, script, new_script, session):
        self._check_perm(script, session)
        if new_script['from_file'] and not script.from_file:
            raise DataError("File scripts must be initiated on the file system.")
        try:
            compile(new_script['live_text'], '<string>', 'exec')
        except SyntaxError as syn_error:
            raise DataError("Syntax Error: {}  text:{}  line: {}  offset: {}".format(syn_error.msg, syn_error.text, syn_error.lineno, syn_error.offset))
        except BaseException as other_error:
            raise DataError("Script Error: {}".format(other_error.msg))
        new_script['approved'] = has_perm(session, 'admin')
        if script.from_file:
            try:
                script.write(new_script['live_text'])
            except EnvironmentError:
                raise DataError("Failed to write new text to file")
        else:
            new_script['text'] = new_script['live_text']

    def post_update(self, script, session):
        script.compile()

    def post_delete(self, del_obj, session):
        script_manager.delete(del_obj)



