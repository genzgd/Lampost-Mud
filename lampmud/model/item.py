import math

from lampost.event.zone import Attachable
from lampost.meta.auto import TemplateField
from lampost.db.dbo import CoreDBO, DBOFacet
from lampost.db.dbofield import DBOField, DBOTField
from lampost.db.template import TemplateInstance
from lampost.gameops.action import obj_action, ActionProvider


def gen_keys(target_id):
    if not target_id:
        return
    target_tuple = tuple(target_id.lower().split(" "))
    prefix_count = len(target_tuple) - 1
    target = target_tuple[prefix_count],
    for x in range(int(math.pow(2, prefix_count))):
        next_prefix = []
        for y in range(prefix_count):
            if int(math.pow(2, y)) & x:
                next_prefix.append(target_tuple[y])
        yield tuple(next_prefix) + target


def target_keys(item):
    t_keys = set(gen_keys(item.title))
    for alias in item.aliases:
        t_keys.update(gen_keys(alias))
    return t_keys


class ItemFacet(DBOFacet, ActionProvider, Attachable):
    sex = DBOField('none')
    flags = DBOField({})

    living = False
    env = None

    general = True

    def _on_loaded(self):
        if not self.target_keys:
            try:
                self.target_keys = target_keys(self)
            except AttributeError:
                pass

    @property
    def name(self):
        return self.title

    def target_finder(self, entity, target_key):
        if target_key in self.target_keys:
            yield self

    def short_desc(self, observer):
        return self.title

    def long_desc(self, observer):
        return self.desc if self.desc else self.title

    def examine(self, source, **_):
        if source.can_see(self):
            source.display_line(self.long_desc(source))

    def glance(self, source, **_):
        if source.can_see(self):
            source.display_line(self.short_desc(source))

    def receive_broadcast(self, broadcast):
        pass

    def social(self, social):
        pass

    def leave_env(self):
        pass


class ItemDBO(CoreDBO, ItemFacet):
    class_id = 'base_item'

    desc = DBOField('')
    title = DBOField('')
    aliases = DBOField([])

    target_keys = set()


class ItemInstance(TemplateInstance, ItemFacet):
    desc = DBOTField('')
    title = DBOTField('')
    aliases = DBOTField([])

    target_keys = TemplateField(set())


class Readable(DBOFacet, ActionProvider):
    class_id = 'readable'

    text = DBOField('')

    @obj_action()
    def read(self, source, **_):
        source.display_line(self.text, "tell_to")
