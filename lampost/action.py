'''
Created on Feb 17, 2012

@author: Geoff
'''

class Action():
            
    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data)             
    
    def __init__(self, verbs, msg_class):
        self.verbs = set()
        if isinstance(verbs, basestring):
            self.add_verb(verbs)
        else:
            for verb in verbs:
                self.add_verb(verb)
        self.msg_class = msg_class         
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))    
                 
    def match(self, words):
        for verb in self.verbs:
            vlen = len(verb)
            if words[:vlen] == verb:
                return verb, words[vlen:]
        return None, None
        
class Examine(Action):
    pass
        
        
    
        
    

    