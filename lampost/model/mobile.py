from lampost.datastore.dbo import RootDBO, DBOList
from lampost.gameops.template import Template
from lampost.model.article import ArticleLoad


class Mobile():

    @property
    def name(self):
        return self.title


class MobileTemplate(Template):
    dbo_key_type = "mobile"

    def config_instance(self, instance):
        instance.baptise(set())
        instance.equip(set())


class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "mob_count", "mob_max"
    dbo_lists = DBOList("article_loads", ArticleLoad),
    mob_count = 1
    mob_max = 1
    article_loads = []
