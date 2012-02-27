'''
Created on Feb 17, 2012

@author: Geoff
'''
class Action():
               
    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data)             
    
    def filter_predicate(self, predicate):
        return True
                
    def match(self, command):
        if not command:
            return False
        words = command.split()
        if words[0] not in self.verbs:
            return False
       
        return self.filter_predicate(words[:1])
    
        
        
        
    
        
    
        
    

    