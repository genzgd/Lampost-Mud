'''
Created on Feb 17, 2012

@author: Geoff
'''
class Action():
               
    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data)             
    
    def build_verbs(self, verbs):
        self.verbs = set()
        if isinstance(verbs, basestring):
            self.add_verb(verbs)
        else:
            for verb in verbs:
                self.add_verb(verb)
               
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))    
            
    def filter_predicate(self, predicate):
        return True
                
    def match(self, words):
        for verb in self.verbs:
            if words[:len(verb)] == verb:
                return verb
    
        
class Examine(Action):
    pass
        
        
    
        
    

    