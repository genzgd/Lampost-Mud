from lampost.datastore.dbo import RootDBO, DBORef
from lampost.gameops.template import Template
from lampost.model.article import ArticleLoad
from lampost.model.creature import Creature
from lampost.util.lmutil import cls_name

class Mobile(Creature):
    def __init__(self, mobile_id):
        self.mobile_id = mobile_id

    @property
    def name(self):
        return self.title


class MobileTemplate(Template, RootDBO):
    template_fields = Mobile.dbo_fields
    dbo_fields = Template.dbo_fields + template_fields
    dbo_key_type = "mobile"
    instance_class = cls_name(Mobile)
    aliases= []

    def config_instance(self, instance):
        instance.baptise(set())
        instance.equip(set())


class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "mob_count", "mob_max"
    dbo_collections = DBORef("article_loads", ArticleLoad),
    article_loads = []
    mob_count = 1
    mob_max = 1

