'''
Created on Feb 17, 2012

@author: Geoff
'''
from message import LMessage, CLASS_BROADCAST

TARGET_ACTION = 1
TARGET_MSG_CLASS = 2
TARGET_ENV = 4
TARGET_ITEM = 8
TARGET_PLAYER = 16
TARGET_MONSTER = 32

TARGET_GENERAL = TARGET_ENV | TARGET_ITEM | TARGET_PLAYER | TARGET_MONSTER
TARGET_LIVING = TARGET_PLAYER | TARGET_MONSTER

class Action():

    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data) 
        
    @staticmethod
    def save_object(obj):
        return Action.datastore.save_object(obj)
        
    @staticmethod
    def load_object(obj):
        return Action.datastore.load_object(obj)
        
    @staticmethod
    def delete_object(obj):
        return Action.datastore.delete_object(obj)          
    
    def __init__(self, verbs, msg_class, target_class):
        self.verbs = set()
        if isinstance(verbs, basestring):
            self.add_verb(verbs)
        else:
            for verb in verbs:
                self.add_verb(verb)
        self.msg_class = msg_class
        self.target_class = target_class
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))    
                  
    def create_message(self, source, verb, target, command):
        return LMessage(source, self.msg_class, target)

class Gesture(Action): 
    def __init__(self, verb):
        self.verbs = set()
        self.add_verb(verb)
        self.msg_class = None
        self.target_class = TARGET_ACTION
  
class SayAction(Action):
    def __init__(self):
        Action.__init__(self, "say", CLASS_BROADCAST, TARGET_ENV)
    
    def create_message(self, source, verb, target, command):
        space_ix = command.find(" ")
        if space_ix == -1:
            return LMessage(source, None, "Say what?")
        statement = command[space_ix + 1:]
        broadcast = "You say `" + statement + "'", source.name + " says, `" + statement + "'"
        return LMessage(source, self.msg_class, target, broadcast)
    