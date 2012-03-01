'''
Created on Feb 26, 2012

@author: Geoff
'''
from message import CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE

class Room():
    def __init__(self, room_id, title, desc):
        self.room_id = room_id;
        self.title = title;
        self.desc = desc;
        self.contents = set()
        self.items = set()
        
    def get_children(self):
        return self.contents.union(self.items)
    
    def accepts(self, lmessage):
        if lmessage.msg_class not in (CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE):
            return False
        if not lmessage.payload:
            return True
            
    def get_targets(self):
        return self
    
    def receive(self, message):
        if message.msg_class == CLASS_SENSE_GLANCE:
            return self.title
        if message.msg_class == CLASS_SENSE_EXAMINE:
            return self.desc
        
    
        
        
        
        
        
        
    
    
        
    