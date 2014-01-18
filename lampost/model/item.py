from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, RootDBOMeta
from lampost.datastore.proto import ProtoField
from lampost.gameops.template import TemplateInstance

m_requires('dispatcher', __name__)


class BaseItem(TemplateInstance):
    __metaclass__ = RootDBOMeta

    desc = DBOField('')
    title = DBOField('')
    aliases = DBOField([])
    sex = DBOField('none')
    target_id = ProtoField()
    target_aliases = ProtoField([])

    living = False
    env = None

    rec_general = True

    @staticmethod
    def config_template(template):
        template.target_id = tuple(unicode(template.title).lower().split(" "))
        template.target_aliases = [tuple(unicode(alias).split(" ")) for alias in template.aliases]

    def rec_examine(self, source, **ignored):
        source.display_line(self.desc if self.desc else self.title)

    def rec_glance(self, source, **ignored):
        if source.can_see(self):
            source.display_line(self.title)

    def rec_broadcast(self, broadcast):
        pass

    def rec_social(self, social):
        pass

    def enter_env(self, new_env, ex=None):
        self.env = new_env
        if new_env:
            self.env.rec_entity_enters(self)

    def leave_env(self, ex=None):
        if self.env:
            self.env = None
            self.env.rec_entity_leaves(self, ex)

    def detach(self):
        self.leave_env()
        detach_events(self)

    def on_loaded(self):
        if not self.target_id:
            self.config_template(self)
