import hashlib
from lampost.editor.editor import ChildrenEditor

from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.gameops.script import compile_script, ShadowScript

m_requires(__name__, 'perm')


def validate(script_dict):
    code, err_str = compile_script(script_dict['text'], script_dict['name'])
    if err_str:
        raise DataError(err_str)
    return code


class ScriptEditor(ChildrenEditor):
    def initialize(self):
        super().initialize(ShadowScript)

    def validate(self):
        validate(self.raw)


