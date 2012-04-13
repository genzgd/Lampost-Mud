'''
Created on Feb 26, 2012

@author: Geoff
'''
from message import CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE, CLASS_MOVEMENT,\
    LMessage, CLASS_ENTER_ROOM, CLASS_LEAVE_ROOM
from dto.display import Display, DisplayLine
from action import TARGET_MSG_CLASS, TARGET_ENV
from datastore.dbo import RootDBO, DBOCollection, DBORef
from movement import Direction


class Exit(RootDBO):
    dbo_fields = "dir_name",
    def __init__(self, dir_name=None, destination=None):
        self.dir_name = dir_name
        self.destination = destination
        self.target_class = TARGET_MSG_CLASS
        
    def short_desc(self, observer=None):
        if observer and getattr(observer, "buildmode", False):
            return "{0}   {1}".format(self.direction.desc, self.destination.dbo_id)
        else:
            return self.direction.desc
    
    def receive(self, message):
        message.source.receive(LMessage(self, CLASS_MOVEMENT, self.destination))
        return self.destination.receive(LMessage(message.source, CLASS_SENSE_EXAMINE))
    
    @property
    def name(self):
        return Direction.ref_map.get(self.dir_name)
    
    @property
    def direction(self):
        return Direction.ref_map.get(self.dir_name)
    

Exit.dbo_base_class = Exit

class Room(RootDBO):
    ROOM_COLOR = 0xAD419A
    ROOM_SEP = "-=" * 30
    EXIT_COLOR = 0x808000
    ITEM_COLOR = 0x7092BE
    
    dbo_key_type = "room"
    dbo_fields = "title", "desc", "dbo_rev"
    dbo_collections = DBOCollection("exits", Exit),
    
    dbo_rev = 0 
    
    def __init__(self, dbo_id, title=None, desc=None):
        self.dbo_id = dbo_id;
        self.title = title;
        self.desc = desc;
        self.contents = []
        self.exits = []
        self.qualifiers = []
        self.target_class = TARGET_ENV
        
    def get_children(self):
        return self.contents + self.exits
    
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_SENSE_GLANCE:
            return Display(self.short_desc(), Room.ROOM_COLOR)
        if lmessage.msg_class == CLASS_SENSE_EXAMINE:
            return self.long_desc(lmessage.source)
        if lmessage.msg_class == CLASS_ENTER_ROOM:           
            self.contents.append(lmessage.payload)
        if lmessage.msg_class == CLASS_LEAVE_ROOM:
            self.contents.remove(lmessage.payload)
        self.tell_contents(lmessage)
        if lmessage.broadcast:
            self.broadcast(lmessage.source, lmessage.payload, lmessage.broadcast)   
     
    def long_desc(self, observer):
        bmode = getattr(observer, "buildmode", False) 
        longdesc = Display(Room.ROOM_SEP, Room.ROOM_COLOR)
        if bmode:
            longdesc.append(DisplayLine("Room Id: " + self.dbo_id))
        longdesc.append(DisplayLine(self.desc, Room.ROOM_COLOR))
        longdesc.append(DisplayLine(Room.ROOM_SEP, Room.ROOM_COLOR))
        if self.exits:
            if bmode:
                for my_exit in self.exits:
                    longdesc.append(DisplayLine("Exit: {0} ".format(my_exit.short_desc(observer)), Room.EXIT_COLOR))
            else:
                longdesc.append(DisplayLine("Obvious exits are: " + self.short_exits(),  Room.EXIT_COLOR))
        else:
            longdesc.append(DisplayLine("No obvious exits", Room.EXIT_COLOR))

        for obj in self.contents:
            if obj != observer:
                longdesc.append(DisplayLine(obj.short_desc(observer), Room.ITEM_COLOR))
        return longdesc
    
    def short_desc(self, observer):
        line = self.title
        if getattr(observer, "buildmode", False):
            line = self.dbo_key + " " + line
        return line
    
    def short_exits(self):
        return ", ".join([ex.short_desc() for ex in self.exits])
    
    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit;
            
    def tell_contents(self, lmessage):
        try:
            for receiver in self.contents:
                if lmessage.source != receiver:
                    receiver.receive(lmessage)
        except Exception:
            pass
    
    def broadcast(self, source, target, broadcast):
        for receiver in self.contents:
            if receiver != source:
                try:
                    receiver.receive_broadcast(source, target, broadcast)
                except AttributeError:
                    pass
                
    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]
        
Room.dbo_base_class = Room
Exit.dbo_refs = DBORef("destination", Room, "room"),