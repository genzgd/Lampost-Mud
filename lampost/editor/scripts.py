import hashlib

from lampost.server.handlers import MethodHandler
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.gameops.script import compile_script, approve_script

m_requires(__name__, 'perm')


def validate(script_dict):
    code, err_str = compile_script(script_dict['text'], script_dict['name'])
    if err_str:
        raise DataError(err_str)
    return code


def validate_scripts(dbo_dict):
    digest = hashlib.md5()
    for script_dict in dbo_dict.get('shadows', []):
        code = validate(script_dict)
        digest.update(script_dict['text'].encode('utf-8'))
        script_dict['script_hash'] = digest.hexdigest()
        approve_script(script_dict['script_hash'], code)


class ScriptEditor(MethodHandler):
    def validate(self):
        validate(self.raw)


