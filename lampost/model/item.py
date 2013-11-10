from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, dbo_describe

m_requires('dispatcher', __name__)


class BaseItem(object):
    template_fields = "desc", "title", "aliases"

    desc = ""
    title = ""
    aliases = []

    sex = "none"
    living = False
    env = None

    target_aliases = []
    rec_general = True

    def rec_examine(self, source, **ignored):
        source.display_line(self.desc if self.desc else self.title)

    def rec_glance(self, source, **ignored):
        if source.can_see(self):
            source.display_line(self.title)

    def rec_describe(self):
        return dbo_describe(self)

    def rec_broadcast(self, broadcast):
        pass

    def rec_social(self, social):
        pass

    def on_loaded(self):
        self.config_targets()

    def config_targets(self):
        self.target_id = tuple(unicode(self.title).lower().split(" "))
        self.target_aliases = [tuple(unicode(alias).split(" ")) for alias in self.aliases]

    def enter_env(self, new_env):
        self.env = new_env
        if new_env:
            self.env.rec_entity_enters(self)

    def leave_env(self):
        if self.env:
            self.env.rec_entity_leaves(self)
        self.env = None

    def detach(self):
        detach_events(self)
        self.env = None


class BaseDBO(BaseItem, RootDBO):
    pass


