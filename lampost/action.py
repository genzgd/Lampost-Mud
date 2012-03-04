'''
Created on Feb 17, 2012

@author: Geoff
'''
from message import LMessage, CLASS_COMM_GENERAL

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
                 
    def match(self, source,  words, command):
        for verb in self.verbs:
            vlen = len(verb)
            if words[:vlen] == verb:
                return self.create_message(source, verb, words[vlen:], command)
        return None
    
    def create_message(self, source, verb, subject, command):
        return LMessage(source, self.msg_class, subject)


class Emotes(Action):
    def __init__(self):
        self.verbMap = {"dance": ("gyrate obscenely!", "gyrates obscenely!"),
                        "blink": ("blink rapidly in surprise.",
                                   "blinks rapidly in surprise")}
        Action.__init__(self, self.verbMap.keys(), CLASS_COMM_GENERAL)
             
    def create_message(self, source, verb, subject, command):
        if subject:
            return None
        opts = self.verbMap[verb[0]]
        payload = CommPayload("You " + opts[0], source.name + " " + opts[1])
        return LMessage(source, self.msg_class, payload, True)

 
class SayAction(Action):
    def __init__(self):
        Action.__init__(self, "say", CLASS_COMM_GENERAL)
    
    def create_message(self, source, verb, subject, command):
        if not subject:
            return None
        payload = CommPayload("You say", source.name + " says",  "`" +
                              command[command.find(" ") + 1:] + "'")
        return LMessage(source, self.msg_class, payload, True)  

    
class CommPayload():
    def __init__(self, self_prefix, other_prefix, text=""):
        self.self_prefix = self_prefix
        self.other_prefix = other_prefix
        self.text = text
        
    def self_text(self):
        return self.self_prefix + " " + self.text
    
    def other_text(self):
        return self.other_prefix + " " + self.text
    
    