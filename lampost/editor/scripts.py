from lampost.server.handlers import MethodHandler
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.gameops.script import compile_script

m_requires(__name__, 'perm')


class ScriptEditor(MethodHandler):
    def validate(self):
        code, err_str = compile_script(self.raw['text'], self.raw['name'])
        if err_str:
            raise DataError(err_str)
