from lampost.di.resource import Injected, module_inject
from lampost.db.exceptions import DataError
from lampost.editor.editor import Editor
from lampmud.comm.broadcast import BroadcastMap, Broadcast, broadcast_types

mud_actions = Injected('mud_actions')
module_inject(__name__)


class SocialsEditor(Editor):
    def __init__(self):
        super().__init__('social')

    @staticmethod
    def preview(source, target, b_map, self_source, **_):
        broadcast = Broadcast(BroadcastMap(**b_map), source, source if self_source else target)
        return {broadcast_type['id']: broadcast.substitute(broadcast_type['id']) for broadcast_type in broadcast_types}

    def _pre_create(self, obj_def, *_):
        if mud_actions.primary(obj_def['dbo_id']):
            raise DataError("Verb already in use")


def _ensure_name(obj_def):
        name = obj_def['name'] or obj_def['verb'] or obj_def['dbo_id']
        obj_def['name'] = name.capitalize


class SkillEditor(Editor):
    def _pre_create(self, obj_def, *_):
        _ensure_name(obj_def)

    def _pre_update(self, obj_def, *_):
        _ensure_name(obj_def)

