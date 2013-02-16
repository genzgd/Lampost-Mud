from lampost.context.resource import requires
from lampost.datastore.dbo import RootDBO

@requires('dispatcher')
class BaseItem(RootDBO):
    dbo_fields = "desc", "title", "aliases"

    desc = ""
    suffix = None
    env = None
    title = ""
    sex = "none"
    living = False
    aliases = []
    target_aliases = []
    rec_general = True

    def rec_examine(self, source, **ignored):
        source.display_line(self.desc if self.desc else self.title)

    def rec_glance(self, source, **ignored):
        source.display_line(self.title)

    def rec_broadcast(self, broadcast):
        pass

    def rec_social(self, social):
        pass

    def on_loaded(self):
        self.config_targets()

    def config_targets(self):
        self.target_id = tuple(unicode(self.title).lower().split(" "))
        if not self.aliases:
            return
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
        self.detach_events(self)
        self.detached = True
        self.env = None


