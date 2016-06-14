import hashlib

from lampost.editor.editor import ChildrenEditor

from lampost.di.resource import Injected, module_inject
from lampost.db.exceptions import DataError
from lampost.gameops.script import compile_script

db = Injected('datastore')
perm = Injected('perm')
module_inject(__name__)


def validate(script_dict):
    code, err_str = compile_script(script_dict['script_hash'], script_dict['text'], script_dict['title'])
    if err_str:
        raise DataError(err_str)
    return code


class ScriptEditor(ChildrenEditor):
    def initialize(self):
        super().initialize('script')

    def _pre_create(self):
        self._calc_hash()
        self.code = validate(self.raw)
        self.raw['approved'] = perm.has_perm(self.player, 'admin') and self.raw['approved']

    def _post_create(self, new_obj):
        new_obj.code = self.code if new_obj.approved else None

    def _pre_update(self, existing):
        self._calc_hash()
        self.code = validate(self.raw)
        holder_keys = db.fetch_set_keys('{}:holders'.format(existing.dbo_key))
        errors = []
        for dbo_key in holder_keys:
            holder = db.load_object(dbo_key)
            if self.raw['cls_type'] != 'any' and self.raw['cls_type'] != holder.class_id:
                errors.append("{} wrong class id {}".format(holder.dbo_id, holder.class_id))
                continue
            if self.raw['cls_shadow'] != 'any_func':
                for shadow_ref in holder.shadow_refs:
                    if shadow_ref.script.dbo_id == existing.dbo_id and shadow_ref.func_name != self.raw['cls_shadow']:
                        errors.append("{} wrong function {}".format(holder.dbo_id, shadow_ref.func_name))
        if errors:
            raise DataError("Incompatible usages must be removed first:  {}".format("  ".join(errors)))
        if self.raw['script_hash'] != existing.script_hash:
            self.raw['approved'] = perm.has_perm(self.player, 'admin') and self.raw['approved']

    def _post_update(self, existing_obj):
        existing_obj.code = self.code if existing_obj.approved else None

    def _calc_hash(self):
        hasher = hashlib.md5()
        hasher.update(self.raw['text'].encode())
        self.raw['script_hash'] = hasher.hexdigest()
