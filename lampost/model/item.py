import math
import itertools

from lampost.context.resource import m_requires
from lampost.datastore.dbo import CoreDBO
from lampost.datastore.dbofield import DBOField, DBOTField
from lampost.datastore.auto import TemplateField, AutoField
from lampost.datastore.meta import CommonMeta
from lampost.gameops.action import obj_action
from lampost.gameops.display import TELL_TO_DISPLAY


m_requires(__name__, 'dispatcher', 'log')


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
    target_keys = set(gen_keys(item.title))
    for alias in item.aliases:
        target_keys.update(gen_keys(alias))
    return target_keys


class BaseItemMixin(metaclass=CommonMeta):
    sex = DBOField('none')
    flags = DBOField({})

    instance_providers = AutoField([])

    living = False
    env = None

    general = True

    @property
    def name(self):
        return self.title

    @property
    def action_providers(self):
        return itertools.chain((getattr(self, func_name) for func_name in self.class_providers), self.instance_providers)

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

    def detach(self):
        self.leave_env()
        detach_events(self)

    def on_loaded(self):
        if not self.target_keys:
            try:
                self.target_keys = target_keys(self)
            except AttributeError:
                pass


class BaseItem(CoreDBO, BaseItemMixin):
    class_id = 'base_item'

    desc = DBOField('')
    title = DBOField('')
    aliases = DBOField([])

    target_keys = {}


class BaseTemplate(CoreDBO, BaseItemMixin):
    desc = DBOTField('')
    title = DBOTField('')
    aliases = DBOTField([])

    target_keys = TemplateField(set())


class Readable(metaclass=CommonMeta):
    mixin_id = 'readable'

    text = DBOField('')

    @obj_action()
    def read(self, source, **_):
        source.display_line(self.text, TELL_TO_DISPLAY)
