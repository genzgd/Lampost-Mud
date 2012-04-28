'''
Created on Feb 17, 2012

@author: Geoff
'''
class Action(object):
    imm_level = 0
    mud = None
    prep = None
 
    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data) 
        
    @staticmethod
    def save_object(obj, update_rev=False):
        return Action.datastore.save_object(obj, update_rev)
        
    @staticmethod
    def create_object(obj):
        return Action.datastore.create_object(obj)
        
    @staticmethod
    def load_object(obj_class, key):
        return Action.datastore.load_object(obj_class, key)
        
    @staticmethod
    def delete_object(obj):
        return Action.datastore.delete_object(obj)          
    
    def __init__(self, verbs, msg_class=None):
        self.verbs = set()
        try:
            self.add_verb(verbs)
        except AttributeError:
            for verb in verbs:
                self.add_verb(verb)
        if msg_class:
            self.msg_class = "rec_{0}".format(msg_class)
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))
        
    def execute(self, target_method, **kwargs):
        if target_method:
            return target_method(**kwargs)

            
class HelpAction(Action):
    def __init__(self):
        Action.__init__(self, "help")
        
    def execute(self, source, args, **ignored):
        action_set = source.actions.get(args)
        if not action_set:
            return "No matching command found"
        if len(action_set) > 1:
            return "Multiple matching commands"
        action = iter(action_set).next()
        return getattr(action, "help_text", "No help available.")
