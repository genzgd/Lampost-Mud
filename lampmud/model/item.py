from lampost.event.zone import Attachable
from lampost.gameops.target import TargetKeys
from lampost.meta.auto import TemplateField
from lampost.db.dbo import CoreDBO, DBOAspect
from lampost.db.dbofield import DBOField, DBOTField
from lampost.db.template import TemplateInstance
from lampost.gameops.action import obj_action, ActionProvider


def target_keys(item):
    t_keys = TargetKeys(item.title)
    for alias in item.aliases:
        t_keys.add(alias)
    return t_keys


class ItemAspect(DBOAspect, ActionProvider, Attachable):
    sex = DBOField('none')
    flags = DBOField({})

    living = False
    env = None

    def _on_loaded(self):
        if not self.target_keys:
            try:
                self.target_keys = target_keys(self)
            except AttributeError:
                pass

    @property
    def name(self):
        return self.title

    def short_desc(self, observer=None):
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


class ItemDBO(CoreDBO, ItemAspect):
    class_id = 'base_item'

    desc = DBOField('')
    title = DBOField('')
    aliases = DBOField([])

    target_keys = None


class ItemInstance(TemplateInstance, ItemAspect):
    desc = DBOTField('')
    title = DBOTField('')
    aliases = DBOTField([])

    target_keys = TemplateField()


class Readable(DBOAspect, ActionProvider):
    class_id = 'readable'

    text = DBOField('')

    @obj_action()
    def read(self, source, **_):
        source.display_line(self.text, "tell_to")
