import itertools

from lampost.core.auto import TemplateField
from lampost.datastore.dbo import CoreDBO, ChildDBO
from lampost.datastore.dbofield import DBOField, DBOTField
from lampost.gameops.action import ActionError
from lampost.gameops.template import Template
from lampost.model.item import target_keys, BaseTemplate
from lampost.util.lputil import plural


VOWELS = {'a', 'e', 'i', 'o', 'u'}


class ArticleTemplate(ChildDBO, Template):
    dbo_key_type = "article"
    dbo_parent_type = "area"

    def plural_name(self, quantity):
        if quantity == 1:
            return self.title
        return self.plural_title

    def on_loaded(self):
        self.single_keys = target_keys(self)
        if self.divisible:
            self.plural_title = plural(self.title)
            self.plural_keys = set()
            for single_key in self.single_keys:
                self.plural_keys.add(single_key[:-1] + (plural(single_key[-1:][0]),))


class Article(BaseTemplate):
    template_id = 'article'

    weight = DBOTField(0)
    value = DBOTField(0)
    divisible = DBOTField(False)
    art_type = DBOTField('treasure')
    level = DBOTField(1)
    quantity = DBOField()
    uses = DBOField()
    single_keys = TemplateField(set())
    plural_keys = TemplateField(set())
    plural_title = TemplateField(None)

    @property
    def name(self):
        if self.quantity and self.quantity > 1:
            prefix = str(self.quantity)
            title = self.plural_title
        elif self.title.lower().startswith(('a ', 'an ')):
            prefix = ""
            title = self.title
        else:
            prefix = "an" if self.title[0] in VOWELS else "a"
            title = self.title
        equipped = ' (equipped)' if self.current_slot else ''
        return "{} {}{}".format(prefix, title,  equipped)

    @property
    def target_keys(self):
        if self.quantity and self.quantity > 1:
            return itertools.chain(self.plural_keys, self.single_keys)
        return self.single_keys

    def short_desc(self, observer=None):
        return self.name.capitalize()

    def long_desc(self, observer=None):
        long_desc = super().long_desc(observer)
        if self.quantity:
            return "{} ({})".format(long_desc, self.quantity)
        return long_desc

    def get(self, source, quantity=None, **_):
        source.check_inven(self, quantity)
        gotten = self
        if quantity and quantity < self.quantity:
            gotten = self.template.create_instance()
            gotten.quantity = quantity
            self.quantity -= quantity
        else:
            source.env.remove_inven(self)
        source.broadcast(s="You pick up {N}", e="{n} picks up {N}", target=gotten)
        gotten.enter_env(source)

    def drop(self, source, quantity=None, **_):
        source.check_drop(self, quantity)
        if self.current_slot:
            raise ActionError("You must unequip the item before dropping it.")
        drop = self.take_from(source, quantity)
        drop.enter_env(source.env)
        source.broadcast(s="You drop {N}", e="{n} drops {N}", target=drop)

    def take_from(self, source, quantity):
        if quantity and quantity < self.quantity:
            self.quantity -= quantity
            drop = self.template.create_instance()
            drop.quantity = quantity
        else:
            drop = self
            source.remove_inven(self)
        return drop

    def enter_env(self, new_env):
        if self.quantity:
            try:
                existing = [item for item in new_env.inven if item.template == self.template][0]
                existing.quantity += self.quantity
                return
            except IndexError:
                pass
        new_env.add_inven(self)


class ArticleReset(CoreDBO):
    class_id = 'article_reset'
    article = DBOField(dbo_class_id='article', required=True)
    reset_count = DBOField(1)
    reset_max = DBOField(1)
    mobile_ref = DBOField(0)
    load_type = DBOField('equip')
