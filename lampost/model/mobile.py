from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.template import Template, TemplateInstance
from lampost.model.article import ArticleLoad
from lampost.model.item import config_targets


class Mobile(TemplateInstance):

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

    def config_instance_cls(self, instance_cls):
        config_targets(instance_cls)

    def config_instance(self, instance, owner):
        instance.baptise()
        instance.equip(set())

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.dbo_id)


class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "reset_count", "reset_max"
    reset_count = 1
    reset_max = 1
    article_loads = DBOField([], ArticleLoad)

    @property
    def reset_key(self):
        return "mobile_resets:{}".format(self.mobile_id)
