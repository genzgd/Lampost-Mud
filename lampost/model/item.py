import math
import itertools

from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, DBOTField
from lampost.datastore.auto import TemplateField, AutoField
from lampost.gameops.action import obj_action
from lampost.gameops.display import TELL_TO_DISPLAY
from lampost.gameops.template import TemplateInstance, TemplateMeta

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


class BaseItemMeta(TemplateMeta):
    def __init__(cls, class_name, bases, new_attrs):
        super().__init__(class_name, bases, new_attrs)
        cls.class_providers = {func.__name__ for func in new_attrs.values() if hasattr(func, 'verbs')}
        for base in bases:
            cls.class_providers.update(getattr(base, 'class_providers', ()))


class BaseItem(TemplateInstance, metaclass=BaseItemMeta):
    class_id = 'base_item'

    desc = DBOTField('')
    title = DBOTField('')
    aliases = DBOTField([])
    sex = DBOTField('none')
    flags = DBOField({})
    target_keys = TemplateField(set())
    instance_providers = AutoField([])

    living = False
    env = None

    general = True

    def __init__(self, dbo_id=None):
        self.target_providers = []
        super().__init__(dbo_id)

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
            self.target_keys = target_keys(self)


class Readable(BaseItem):
    class_id = 'readable'

    text = DBOField('')

    @obj_action()
    def read(self, source, **_):
        source.display_line(self.text, TELL_TO_DISPLAY)
