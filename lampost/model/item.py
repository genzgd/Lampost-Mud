import math
import itertools

from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBOMeta
from lampost.datastore.proto import ProtoField
from lampost.gameops.action import item_actions
from lampost.gameops.display import TELL_TO_DISPLAY
from lampost.gameops.template import TemplateInstance

m_requires('dispatcher', __name__)


def gen_keys(target_id):
    if not target_id:
        return
    target_tuple = tuple(unicode(target_id).lower().split(" "))
    prefix_count = len(target_tuple) - 1
    target = target_tuple[prefix_count],
    for x in range(0, int(math.pow(2, prefix_count))):
        next_prefix = []
        for y in range(0, prefix_count):
            if int(math.pow(2, y)) & x:
                next_prefix.append(target_tuple[y])
        yield tuple(next_prefix) + target


class BaseItem(TemplateInstance):
    _class_providers = []
    desc = DBOField('')
    title = DBOField('')
    aliases = DBOField([])
    sex = DBOField('none')
    target_keys = ProtoField(set())

    living = False
    env = None

    rec_general = True

    @staticmethod
    def config_template(template):
        template.target_keys = set(gen_keys(template.title))
        for alias in template.aliases:
            template.target_keys.update(gen_keys(alias))

    def rec_examine(self, source, **ignored):
        source.display_line(self.desc if self.desc else self.title)

    def rec_glance(self, source, **ignored):
        if source.can_see(self):
            source.display_line(self.title)

    def rec_broadcast(self, broadcast):
        pass

    def rec_social(self, social):
        pass

    def enter_env(self, new_env, ex=None):
        self.env = new_env
        if new_env:
            self.env.rec_entity_enters(self)

    def leave_env(self, ex=None):
        if self.env:
            old_env = self.env
            self.env = None
            old_env.rec_entity_leaves(self, ex)

    def detach(self):
        self.leave_env()
        detach_events(self)

    def on_loaded(self):
        if not self.target_keys:
            self.config_template(self)

    def _action_providers(self):
        return []

    @property
    def action_providers(self):
        return itertools.chain(self._class_providers, self._action_providers())



@item_actions('read')
class Readable(BaseItem):
    text = DBOField('')

    def rec_read(self, source, **ignored):
        source.display_line(self.text, TELL_TO_DISPLAY)
