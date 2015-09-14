import hashlib

from lampost.editor.editor import ChildrenEditor

from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.gameops.script import compile_script, ShadowScript

m_requires(__name__, 'perm')


def validate(script_dict):
    code, err_str = compile_script(script_dict['script_hash'], script_dict['text'], script_dict['title'])
    if err_str:
        raise DataError(err_str)
    return code


class ScriptEditor(ChildrenEditor):
    def initialize(self):
        super().initialize(ShadowScript)

    def _pre_create(self):
        self._calc_hash()
        self.code = validate(self.raw)
        self.raw['approved'] = has_perm(self.player, 'admin') and self.raw['approved']

    def _post_create(self, new_obj):
        new_obj.code = self.code if new_obj.approved else None

    def _pre_update(self, existing):
        self.code = validate(self.raw)
        self._calc_hash()
        if self.raw['script_hash'] != existing.script_hash:
            self.raw['approved'] = has_perm(self.player, 'admin') and self.raw['approved']

    def _post_update(self, existing_obj):
        existing_obj.code = self.code if existing_obj.approved else None

    def _calc_hash(self):
        hasher = hashlib.md5()
        hasher.update(self.raw['text'].encode())
        self.raw['script_hash'] = hasher.hexdigest()