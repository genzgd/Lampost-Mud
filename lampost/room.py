'''
Created on Feb 26, 2012

@author: Geoff
'''
from message import CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE, CLASS_MOVEMENT,\
    LMessage, CLASS_ENTER_ROOM, CLASS_LEAVE_ROOM, CLASS_COMM_GENERAL
from responder import Responder
from dto.display import Display, DisplayLine

class Room():
    ROOM_COLOR = 0xAD419A
    ROOM_SEP = "-=" * 30
    EXIT_COLOR = 0x808000
    ITEM_COLOR = 0x7092BE
    
    def __init__(self, room_id, title, desc):
        self.room_id = room_id;
        self.title = title;
        self.desc = desc;
        self.contents = set()
        self.items = set()
        self.exits = set()
        
    def get_children(self):
        return self.contents.union(self.items, self.exits)
    
    def accepts(self, lmessage):
        if lmessage.msg_class not in (CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE,
            CLASS_COMM_GENERAL):
            return False
        if not lmessage.target_id:
            return True
            
    def get_targets(self):
        return self
    
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_SENSE_GLANCE:
            return Display(self.title, Room.ROOM_COLOR)
        if lmessage.msg_class == CLASS_SENSE_EXAMINE:
            return self.long_desc(lmessage.source)
        if lmessage.msg_class == CLASS_ENTER_ROOM:           
            self.contents.add(lmessage.payload)
        if lmessage.msg_class == CLASS_LEAVE_ROOM:
            self.contents.remove(lmessage.payload)
        self.tell_contents(lmessage)    
     
    def long_desc(self, observer):
        longdesc = Display(Room.ROOM_SEP, Room.ROOM_COLOR)
        longdesc.append(DisplayLine(self.desc, Room.ROOM_COLOR))
        longdesc.append(DisplayLine(Room.ROOM_SEP, Room.ROOM_COLOR))
        if self.exits:
            exitline = "Obvious exits are: "
            for ex in self.exits:
                exitline = exitline + ex.dirdesc()
                longdesc.append(DisplayLine(exitline, Room.EXIT_COLOR))
        for obj in self.contents:
            if obj != observer:
                longdesc.append(DisplayLine(obj.short_desc(), Room.ITEM_COLOR))
        return longdesc
    
    def tell_contents(self, lmessage):
        try:
            for receiver in self.contents.union(self.items):
                if lmessage.source != receiver:
                    receiver.receive(lmessage)
        except Exception:
            pass
    
    def broadcast(self, source, target, broadcast):
        try:
            for receiver in self.contents:
                if receiver != source:
                    receiver.receive_broadcast(source, target, broadcast)
        except Exception:
            pass
        
             
class Exit(Responder):
    def __init__(self, direction, destination):
        self.msg_class = direction
        self.destination = destination
        
    def dirdesc(self):
        return self.msg_class.desc
        
    def receive(self, message):
        message.source.receive(LMessage(self, CLASS_MOVEMENT, self.destination))
        return self.destination.receive(LMessage(message.source, CLASS_SENSE_EXAMINE, None))
        