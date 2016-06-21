import hashlib

from lampost.editor.editor import ChildrenEditor

from lampost.di.resource import Injected, module_inject
from lampost.db.exceptions import DataError
from lampost.gameops.script import compile_script

db = Injected('datastore')
perm = Injected('perm')
module_inject(__name__)


class ScriptEditor(ChildrenEditor):
    def initialize(self):
        super().initialize('script')

    def _validate(self):
        hasher = hashlib.md5()
        hasher.update(self.raw['text'].encode())
        self.raw['script_hash'] = hasher.hexdigest()
        self.code, err_str = compile_script(self.raw['script_hash'], self.raw['text'], self.raw['title'])
        if err_str:
            raise DataError(err_str)

    def _pre_create(self):
        self._validate()
        self.raw['approved'] = perm.has_perm(self.player, 'admin') and self.raw['approved']

    def _post_create(self, new_obj):
        new_obj.code = self.code if new_obj.approved else None

    def _pre_update(self, existing):
        self._validate()
        holder_keys = db.fetch_set_keys('{}:holders'.format(existing.dbo_key))
        if self.raw['cls_type'] != 'any':
            errors = []
            for dbo_key in holder_keys:
                holder = db.load_object(dbo_key)
                for script_ref in getattr(holder, "script_refs", ()):
                    if script_ref.script.dbo_id == existing.dbo_id:
                        if self.raw['cls_type'] != holder.class_id:
                            errors.append("{} wrong class id {}".format(holder.dbo_id, holder.class_id))
                        elif script_ref.func_name != self.raw['cls_shadow']:
                            errors.append("{} wrong function {}".format(holder.dbo_id, script_ref.func_name))
            if errors:
                raise DataError("Incompatible usages must be removed first:  {}".format("  ".join(errors)))
        if self.raw['script_hash'] != existing.script_hash:
            self.raw['approved'] = perm.has_perm(self.player, 'admin') and self.raw['approved']

    def _post_update(self, existing_obj):
        existing_obj.code = self.code if existing_obj.approved else None
