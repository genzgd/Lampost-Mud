from item import BaseItem
from lampost.gameops.action import ActionError
from lampost.datastore.dbo import RootDBO
from lampost.gameops.template import Template
from lampost.util.lmutil import cls_name

VOWELS = {'a', 'e', 'i', 'o', 'u', 'y'}


class Article(BaseItem):
    template_fields = "weight", "slot", "equip_slot", "art_type", "level"

    weight = 0
    slot = "none"
    art_type = "treasure"
    level = 1

    rec_wear = True
    equip_slot = None


    @property
    def name(self):
        return self.title

    def short_desc(self, observer=None):
        if self.title.lower().startswith(('a', 'an')):
            prefix = ""
        else:
            prefix = "An" if self.title[0] in VOWELS else "A"
        equipped = ' (equipped)' if self.equip_slot else ''
        return "{0} {1}.{2}".format(prefix, self.title, equipped)

    @property
    def rec_get(self):
        if self.env:
            return self.do_rec_get
        return None

    def do_rec_get(self, source):
        check_result = source.check_inven(self)
        if check_result:
            return check_result
        return source.add_inven(self)

    @property
    def rec_drop(self):
        if self.env:
            return None
        return self.do_rec_drop

    def do_rec_drop(self, source):
        if self.equip_slot:
            raise ActionError("You must unequip the item before dropping it.")
        return source.drop_inven(self)


class Container(Article):
    def __init__(self, dbo_id):
        self.contents = []


class ArticleTemplate(Template, RootDBO):
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


class ArticleReset(RootDBO):
    dbo_fields = "article_id", "reset_count", "reset_max"
    reset_count = 1
    reset_max = 1

    @property
    def reset_key(self):
        return "article_resets:{}".format(self.article_id)


class ArticleLoad(RootDBO):
    dbo_fields = 'article_id', 'load_type', 'count'
    count = 1
    load_type = 'equip'
