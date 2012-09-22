'''
Created on Apr 13, 2012

@author: Geoff
'''
from item import BaseItem
from lampost.datastore.dbo import RootDBO
from lampost.gameops.template import Template

VOWELS = {'a', 'e', 'i', 'o', 'u', 'y'}

class Article(BaseItem):
    dbo_rev = 0
    dbo_fields = BaseItem.dbo_fields + ("weight",)
    weight = 0

    def __init__(self, article_id):
        self.article_id = article_id

    def short_desc(self, observer=None):
        if self.title.lower().startswith(('a', 'an')):
            prefix = ""
        else:
            prefix = "An" if self.title[0] in VOWELS else "A"
        return "{0} {1}.".format(prefix, self.title)

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
        return source.drop_inven(self)

class Container(Article):
    def __init__(self):
        self.contents = []


class ArticleTemplate(RootDBO, Template):
    dbo_key_type = "article"
    dbo_rev = 0
    instance_class = ".".join([Article.__module__, Article.__name__]) #@UndefinedVariable
    aliases= []

    def __init__(self, dbo_id, title=None, desc=None, instance_class=None):
        self.dbo_id = dbo_id
        self.article_id = dbo_id
        self.title = title
        self.desc = desc
        if instance_class:
            self.instance_class = ".".join([instance_class.__module__, instance_class.__name__])


class ArticleReset(RootDBO):
    dbo_fields = "article_id", "article_count", "article_max"
    article_count = 1
    article_max = 1

    def __init__(self, article_id=None, article_count=None, article_max=None):
        self.article_id = article_id
        if article_count is not None:
            self.article_count = article_count
        if article_max:
            self.article_max = article_max
