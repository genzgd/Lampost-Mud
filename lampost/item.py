'''
Created on Mar 11, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO

class BaseItem(RootDBO):
    dbo_fields = "desc", "title", "aliases"
    
    desc = ""
    suffix = None
    title = ""
    sex = "none"
    aliases = []

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
        
    def register(self, event_type, callback):
        registration = self.dispatcher.register(event_type, callback)
        self.registrations.add(registration)
        return registration
        
    def unregister_type(self, event_type, callback):
        detach_set = set()
        for reg in self.registrations:
            if reg.event_type == event_type and reg.callback == callback:
                reg.detach()
                detach_set.add(reg)
        self.registrations.difference_update(detach_set)
        
    def unregister(self, registration):
        registration.detach()
        self.registrations.remove(registration)
                 
    def register_p(self, freq, callback):
        registration = self.dispatcher.register_p(freq, callback)
        self.registrations.add(registration)
        return registration      
        
    def short_desc(self, observer):
        return self.title
           
    def long_desc(self, observer):
        return self.desc if self.desc else self.title
        
        