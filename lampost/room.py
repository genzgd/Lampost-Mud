'''
Created on Feb 26, 2012

@author: Geoff
'''
from message import CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE, CLASS_MOVEMENT,\
    LMessage
from responder import Responder
from dto.display import Display, DisplayLine

class Room():
    ROOM_COLOR = 0xAD419A
    ROOM_SEP = "-=" * 30
    EXIT_COLOR = 0x808000
    
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
        if lmessage.msg_class not in (CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE):
            return False
        if not lmessage.payload:
            return True
            
    def get_targets(self):
        return self
    
    def receive(self, message):
        if message.msg_class == CLASS_SENSE_GLANCE:
            return Display(self.title, Room.ROOM_COLOR)
        if message.msg_class == CLASS_SENSE_EXAMINE:
            longdesc = Display(Room.ROOM_SEP, Room.ROOM_COLOR)
            longdesc.append(DisplayLine(self.desc, Room.ROOM_COLOR))
            longdesc.append(DisplayLine(Room.ROOM_SEP, Room.ROOM_COLOR))
            if self.exits:
                exitline = "Obvious exits are "
                for ex in self.exits:
                    exitline = exitline + ex.dirdesc()
                longdesc.append(DisplayLine(exitline, Room.EXIT_COLOR))
            return longdesc
        

class Exit(Responder):
    def __init__(self, direction, destination):
        self.msg_class = direction
        self.destination = destination
        
    def dirdesc(self):
        return self.msg_class.desc
        
    def receive(self, message):
        message.source.receive(LMessage(self, CLASS_MOVEMENT, self.destination))
        return self.destination.receive(LMessage(message.source, CLASS_SENSE_EXAMINE, None))
        
