from lampost.datastore.proto import ProtoField
from lampost.model.item import BaseItem, target_keys
from lampost.gameops.action import ActionError
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.template import Template
from lampost.util.lmutil import plural

VOWELS = {'a', 'e', 'i', 'o', 'u'}


class ArticleTemplate(Template):
    dbo_key_type = "article"

    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]

    @property
    def dbo_set_key(self):
        return "area_articles:{}".format(self.area_id)

    @property
    def reset_key(self):
        return "article_resets:{}".format(self.dbo_id)

    def on_loaded(self):
        self.single_keys = target_keys(self)
        if self.divisible:
            self.plural_title = plural(self.title)
            self.plural_keys = set()
            for single_key in self.single_keys:
                self.plural_keys.add(single_key[:-1] + (plural(single_key[-1:][0]),))
        super(ArticleTemplate, self).on_loaded()


class Article(BaseItem):
    template_class = ArticleTemplate

    weight = DBOField(0)
    divisible = DBOField(False)
    equip_slot = DBOField('none')
    art_type = DBOField('treasure')
    level = DBOField(1)
    current_slot = DBOField()
    quantity = DBOField()
    uses = DBOField()
    single_keys = ProtoField(set())
    plural_keys = ProtoField(set())
    plural_title = ProtoField(None)

    @property
    def name(self):
        if self.quantity:
            prefix = unicode(self.quantity)
            title = self.plural_title
        elif self.title.lower().startswith(('a ', 'an ')):
            prefix = ""
            title = self.title
        else:
            prefix = "an" if self.title[0] in VOWELS else "a"
            title = self.title
        equipped = ' (equipped)' if self.current_slot else ''
        return "{} {}.{}".format(prefix, title,  equipped)

    @property
    def target_keys(self):
        if self.quantity > 1:
            return self.plural_keys
        return self.single_keys

    def short_desc(self, observer=None):
        return self.name.capitalize()

    def long_desc(self, observer=None):
        long_desc = super(Article, self).long_desc(observer)
        if self.quantity:
            return "{} ({})".format(long_desc, self.quantity)
        return long_desc

    def rec_get(self, source, quantity=None, **ignored):
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

    def rec_drop(self, source, quantity=None, **ignored):
        source.check_drop(self, quantity)
        if self.current_slot:
            raise ActionError("You must unequip the item before dropping it.")

        if quantity and quantity < self.quantity:
            self.quantity -= quantity
            drop = self.template.create_instance()
            drop.quantity = quantity
        else:
            drop = self
            source.remove_inven(self)
        drop.enter_env(source.env)
        source.broadcast(s="You drop {N}", e="{n} drops {N}", target=drop)

    def enter_env(self, new_env):
        if self.quantity:
            try:
                existing = [item for item in new_env.inven if item.template == self.template][0]
                existing.quantity += self.quantity
                return
            except IndexError:
                pass
        new_env.add_inven(self)

    def rec_wear(self):
        pass

    def rec_remove(self):
        pass


class ArticleReset(RootDBO):
    article_id = DBOField()
    reset_count = DBOField(1)
    reset_max = DBOField(1)

    @property
    def reset_key(self):
        return "article_resets:{}".format(self.article_id)


class ArticleLoad(RootDBO):
    article_id = DBOField()
    count = DBOField(1)
    load_type = DBOField('equip')
