import math
import itertools

from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBOMeta, DBOTField
from lampost.datastore.auto import TemplateField
from lampost.gameops.action import item_action, make_action
from lampost.gameops.display import TELL_TO_DISPLAY
from lampost.gameops.target import im_self_finder
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


def target_keys(item):
    target_keys = set(gen_keys(item.title))
    for alias in item.aliases:
        target_keys.update(gen_keys(alias))
    return target_keys


class BaseItemMeta(RootDBOMeta):
    def __init__(cls, class_name, bases, new_attrs):
        super(BaseItemMeta, cls).__init__(class_name, bases, new_attrs)
        cls._class_providers = {func.func_name for func in new_attrs.viewvalues() if hasattr(func, 'verbs')}
        for base in bases:
            cls._class_providers.update(getattr(base, '_class_providers', ()))


class BaseItem(TemplateInstance):
    __metaclass__ = BaseItemMeta
    desc = DBOTField('')
    title = DBOTField('')
    aliases = DBOTField([])
    sex = DBOTField('none')
    target_keys = TemplateField(set())

    living = False
    env = None

    rec_general = True

    def __init__(self, dbo_id=None):
        self.action_providers = [getattr(self, func_name) for func_name in self._class_providers]
        self.target_providers = []
        super(BaseItem, self).__init__(dbo_id)

    def target_finder(self, entity, target_key):
        if target_key in self.target_keys:
            yield self

    def short_desc(self, observer):
        return self.title

    def long_desc(self, observer):
        return self.desc if self.desc else self.title

    def rec_examine(self, source, **ignored):
        if source.can_see(self):
            source.display_line(self.long_desc(source))

    def rec_glance(self, source, **ignored):
        if source.can_see(self):
            source.display_line(self.short_desc(source))

    def rec_broadcast(self, broadcast):
        pass

    def rec_social(self, social):
        pass

    def detach(self):
        self.leave_env()
        detach_events(self)

    def on_loaded(self):
        if not self.target_keys:
            self.target_keys = target_keys(self)


class Readable(BaseItem):
    text = DBOField('')

    @item_action()
    def rec_read(self, source, **ignored):
        source.display_line(self.text, TELL_TO_DISPLAY)
