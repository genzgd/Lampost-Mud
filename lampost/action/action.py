'''
Created on Feb 17, 2012

@author: Geoff
'''
class Action(object):
    imm_level = 0
    mud = None

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
