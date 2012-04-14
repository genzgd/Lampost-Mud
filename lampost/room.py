'''
Created on Feb 26, 2012

@author: Geoff
'''
from message import CLASS_SENSE_GLANCE, CLASS_SENSE_EXAMINE, CLASS_MOVEMENT,\
    LMessage, CLASS_ENTER_ROOM, CLASS_LEAVE_ROOM
from dto.display import Display, DisplayLine
from action import TARGET_MSG_CLASS, TARGET_ENV
from datastore.dbo import RootDBO, DBORef
from movement import Direction
from mobile import MobileReset


class Exit(RootDBO):
    dbo_fields = "dir_name",
    target_class = TARGET_MSG_CLASS
    
    def __init__(self, direction=None, destination=None):
        self.direction = direction
        self.destination = destination
    
    @property
    def dir_name(self):
        return self.direction.key
    
    @dir_name.setter
    def dir_name(self, value):
        self.direction = Direction.ref_map[value]
              
    def short_desc(self, observer=None):
        if observer and getattr(observer, "buildmode", False):
            return "{0}   {1}".format(self.direction.desc, self.destination.dbo_id)
        else:
            return self.direction.desc
    
    def receive(self, message):
        message.source.receive(LMessage(self, CLASS_MOVEMENT, self.destination))
        return self.destination.receive(LMessage(message.source, CLASS_SENSE_EXAMINE))
    
    @property
    def target_id(self):
        return self.direction


class Room(RootDBO):
    ROOM_COLOR = 0xAD419A
    ROOM_SEP = "-=" * 30
    EXIT_COLOR = 0x808000
    ITEM_COLOR = 0x7092BE
    
    dbo_key_type = "room"
    dbo_fields = "title", "desc", "dbo_rev"
    dbo_collections = DBORef("exits", Exit), DBORef("mobile_resets", MobileReset)
    
    dbo_rev = 0 
    
    target_class = TARGET_ENV
    
    def __init__(self, dbo_id, title=None, desc=None):
        self.dbo_id = dbo_id;
        self.title = title;
        self.desc = desc;
        self.contents = []
        self.exits = []
        self.mobile_resets = []
        
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
                      
    def refresh(self):
        for entity in self.contents:
            try:
                entity.refresh_env()
            except AttributeError:
                pass
                   
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
                    
    def reset(self, area):
        for mreset in self.mobile_resets:
            curr_count = len([inhabitent for inhabitent in self.contents if getattr(inhabitent, "mobile_id", None) == mreset.mobile_id])
            for unused in range(mreset.mob_count - curr_count):
                area.create_mob(mreset.mobile_id, self)
            if curr_count + 1 < mreset.mob_max:
                area.create_mob(mreset.mobile_id, self)
                                   
    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]
        
Exit.dbo_refs = DBORef("destination", Room, "room"),