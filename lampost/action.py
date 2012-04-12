'''
Created on Feb 17, 2012

@author: Geoff
'''
from message import LMessage, CLASS_BROADCAST

TARGET_SELF = 1
TARGET_ACTION = 2
TARGET_MSG_CLASS = 4
TARGET_ENV = 8
TARGET_ITEM = 16
TARGET_PLAYER = 32
TARGET_MONSTER = 64

TARGET_GENERAL = TARGET_ENV | TARGET_ITEM | TARGET_PLAYER | TARGET_MONSTER
TARGET_LIVING = TARGET_PLAYER | TARGET_MONSTER

class Action():
    imm_level = 0

    @staticmethod 
    def dispatch(event_type, data):
        Action.dispatcher.dispatch(event_type, data) 
        
    @staticmethod
    def save_object(obj):
        return Action.datastore.save_object(obj)
        
    @staticmethod
    def load_object(obj_class, key):
        return Action.datastore.load_object(obj_class, key)
        
    @staticmethod
    def delete_object(obj):
        return Action.datastore.delete_object(obj)          
    
    
    def __init__(self, verbs, msg_class, action_class):
        self.verbs = set()
        try:
            self.add_verb(verbs)
        except:
            for verb in verbs:
                self.add_verb(verb)
        self.msg_class = msg_class
        self.action_class = action_class
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))    
                  
    def create_message(self, source, verb, target, command):
        return LMessage(source, self.msg_class, target)
   

class Gesture(Action): 
    def __init__(self, verb):
        self.verbs = set()
        self.add_verb(verb)
        self.msg_class = None
        self.action_class = TARGET_ACTION
        
    def create_message(self, source, verb, target, command):
        return self.execute(source, target)
      
class SayAction(Action):
    def __init__(self):
        Action.__init__(self, "say", CLASS_BROADCAST, TARGET_ENV)
    
    def create_message(self, source, verb, target, command):
        space_ix = command.find(" ")
        if space_ix == -1:
            return "Say what?"
        statement = command[space_ix + 1:]
        broadcast = "You say `" + statement + "'", source.name + " says, `" + statement + "'"
        return LMessage(source, self.msg_class, target, broadcast)
 
