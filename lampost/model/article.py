from item import BaseItem
from lampost.action.action import ActionError
from lampost.datastore.dbo import RootDBO
from lampost.gameops.template import Template
from lampost.util.lmutil import cls_name

VOWELS = {'a', 'e', 'i', 'o', 'u', 'y'}

class Article(BaseItem):
    dbo_fields = BaseItem.dbo_fields + ("weight", "slot", "equip_slot", "type")
    rec_wear = True
    equip_slot = None

    def __init__(self, article_id):
        self.article_id = article_id

    def short_desc(self, observer=None):
        if self.title.lower().startswith(('a', 'an')):
            prefix = ""
        else:
            prefix = "An" if self.title[0] in VOWELS else "A"
        equipped = ' (equipped)' if self.equip_slot else ''
        return "{0} {1}.{2}".format(prefix, self.title, equipped)

    @property
    def name(self):
        return self.title

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
    def __init__(self):
        self.contents = []


class ArticleTemplate(Template, RootDBO):
    template_fields = Article.dbo_fields
    dbo_fields = Template.dbo_fields + template_fields
    dbo_key_type = "article"
    instance_class = cls_name(Article)
    aliases= []
    weight = 0
    slot = "none"
    type = "treasure"


class ArticleReset(RootDBO):
    dbo_fields = "article_id", "article_count", "article_max"
    article_count = 1
    article_max = 1
