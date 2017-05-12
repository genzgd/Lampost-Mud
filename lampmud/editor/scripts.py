import hashlib

from lampost.editor.editor import ChildrenEditor

from lampost.di.resource import Injected, module_inject
from lampost.db.exceptions import DataError
from lampost.gameops.script import compile_script

db = Injected('datastore')
perm = Injected('perm')
module_inject(__name__)


def _validate(obj_def):
    hasher = hashlib.md5()
    hasher.update(obj_def['text'].encode())
    obj_def['script_hash'] = hasher.hexdigest()
    _, err_str = compile_script(obj_def['script_hash'], obj_def['text'], obj_def['title'])
    if err_str:
        raise DataError(err_str)


class ScriptEditor(ChildrenEditor):
    def __init__(self):
        super().__init__('script')

    def _pre_create(self, obj_def, session):
        _validate(obj_def)
        obj_def['approved'] = perm.has_perm(session.player, 'admin') and obj_def['approved']

    def _pre_update(self, obj_def, existing, session):
        _validate(obj_def)
        holder_keys = db.fetch_set_keys('{}:holders'.format(existing.dbo_key))
        if obj_def['builder'] == 'shadow':
            cls_type = obj_def['metadata']['cls_type']
            cls_shadow = obj_def['metadata']['cls_shadow']
            errors = []
            for dbo_key in holder_keys:
                holder = db.load_object(dbo_key)
                for script_ref in getattr(holder, "script_refs", ()):
                    if script_ref.script.dbo_id == existing.dbo_id:
                        if cls_type != holder.class_id:
                            errors.append("{} wrong class id {}".format(holder.dbo_id, holder.class_id))
                        elif script_ref.func_name != cls_shadow:
                            errors.append("{} wrong function {}".format(holder.dbo_id, script_ref.func_name))
            if errors:
                raise DataError("Incompatible usages must be removed first:  {}".format("  ".join(errors)))
        if obj_def['script_hash'] != existing.script_hash:
            obj_def['approved'] = perm.has_perm(session.player, 'admin') and obj_def['approved']

