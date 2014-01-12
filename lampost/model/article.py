from lampost.model.item import BaseItem
from lampost.gameops.action import ActionError
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.template import Template

VOWELS = {'a', 'e', 'i', 'o', 'u', 'y'}


class Article(BaseItem):

    weight = DBOField(0)
    equip_slot = DBOField('none')
    art_type = DBOField('treasure')
    level = DBOField(1)
    current_slot = DBOField()

    @property
    def name(self):
        return self.title

    def short_desc(self, observer=None):
        if self.title.lower().startswith(('a', 'an')):
            prefix = ""
        else:
            prefix = "An" if self.title[0] in VOWELS else "A"
        equipped = ' (equipped)' if self.current_slot else ''
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
