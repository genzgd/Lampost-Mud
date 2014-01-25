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

    @property
    def rec_get(self):
        if self.env:
            return self.do_rec_get
        return None

    def do_rec_get(self, source, quantity=None):
        source.check_inven(self, quantity)
        source.add_inven(self)

    def rec_wear(self):
        pass

    def rec_remove(self):
        pass

    @property
    def rec_drop(self):
        if self.env:
            return None
        return self.do_rec_drop

    def do_rec_drop(self, source):
        if self.current_slot:
            raise ActionError("You must unequip the item before dropping it.")
        return source.drop_inven(self)

    def enter_env(self, env, ex=None):
        if self.divisible and not self.quantity:
            return
        return super(Article, self).enter_env(env, ex)


    def add_quantity(self, quantity):
        if self.quantity:
            self.leave_env(self.env)
            self.quantity += quantity
        else:
            self.quantity = quantity
        self.enter_env(self.env)


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
