from lampost.context.resource import requires
from lampost.datastore.dbo import RootDBO

@requires('dispatcher', 'datastore')
class BaseItem(RootDBO):
    dbo_fields = "desc", "title", "aliases"
    
    desc = ""
    suffix = None
    env = None
    title = ""
    sex = "none"
    aliases = []
    target_aliases = []

    def rec_social(self, source, **ignored):
        pass
        
    def rec_examine(self, source, **ignored):
        return self.long_desc(source)
    
    def rec_glance(self, source, **ignored):
        return self.short_desc(source)
        
    def rec_broadcast(self, broadcast):
        pass
 
    def on_loaded(self):
        self.config_targets()
        
    def config_targets(self):
        self.target_id = tuple(self.title.lower().split(" "))
        if not self.aliases:
            return
        self.target_aliases = [tuple(alias.split(" ")) for alias in self.aliases]

    def short_desc(self, observer):
        return self.title
           
    def long_desc(self, observer):
        return self.desc if self.desc else self.title
        
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

        
        