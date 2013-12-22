from lampost.datastore.dbo import RootDBO, DBOList
from lampost.gameops.template import Template
from lampost.model.article import ArticleLoad


class Mobile():

    @property
    def name(self):
        return self.title


class MobileTemplate(Template, RootDBO):
    dbo_key_type = "mobile"

    @property
    def dbo_set_key(self):
        return "area_mobiles:{}".format(self.area_id)

    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]

    def config_instance(self, instance):
        instance.baptise()
        instance.equip(set())

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.dbo_id)


class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "reset_count", "reset_max"
    dbo_lists = DBOList("article_loads", ArticleLoad),
    reset_count = 1
    reset_max = 1
    article_loads = []

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.mobile_id)
