from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.editor import Editor
from lampost.comm.broadcast import BroadcastMap, Broadcast, broadcast_types
from lampost.mud.socials import Social

m_requires(__name__, 'mud_actions')


class SocialsEditor(Editor):
    def initialize(self):
        super().initialize(Social)

    def preview(self):
        content = self._content()
        broadcast = Broadcast(BroadcastMap(**content.b_map), content.source, content.source if content.self_source else content.target)
        return {broadcast_type['id']: broadcast.substitute(broadcast_type['id']) for broadcast_type in broadcast_types}

    def _pre_create(self):
        if (self.raw['dbo_id'],) in mud_actions:
            raise DataError("Verb already in use")

    def _post_delete(self, social):
        del mud_actions[(social.dbo_id,)]


class SkillEditor(Editor):
    def _pre_create(self):
        self._ensure_name()

    def _pre_update(self, _):
        self._ensure_name()

    def _ensure_name(self):
        name = self.raw['name'] or self.raw['verb'] or self.raw['dbo_id']
        self.raw['name'] = name.capitalize()

