from lampost.datastore.dbo import RootDBO, DBORef
from lampost.gameops.template import Template
from lampost.model.article import ArticleLoad
from lampost.model.entity import Entity
from lampost.util.lmutil import cls_name


class Mobile():

    @property
    def name(self):
        return self.title


class MobileTemplate(Template, RootDBO):
    dbo_key_type = "mobile"
    sex = 'none'
    size = 'medium'

    def __init__(self, dbo_id):
        super(MobileTemplate, self).__init__(dbo_id)
        self.aliases = []

    def config_instance(self, instance):
        instance.baptise(set())
        instance.equip(set())


class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "mob_count", "mob_max"
    dbo_collections = DBORef("article_loads", ArticleLoad),
    mob_count = 1
    mob_max = 1

    def __init__(self):
        super(MobileReset, self).__init__()
        self.article_loads = []