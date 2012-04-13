'''
Created on Apr 8, 2012

@author: Geoffrey
'''
from action import Gesture
from immortal import IMM_LEVELS
from movement import Direction
from player import Player
from room import Room, Exit
from lmutil import ljust
from dto.display import Display, DisplayLine
from dialog import Dialog, DIALOG_TYPE_CONFIRM
from message import DialogMessage

BUILD_ROOM = Room("buildroom")

class BuildMode(Gesture):
    def __init__(self):
        Gesture.__init__(self, "buildmode")
        
    def execute(self, builder, args):
        current = getattr(builder, "buildmode", False)
        builder.buildmode = not current
        return "Build Mode is {0}".format("On" if builder.buildmode else "Off")


class RoomList(Gesture):
    def __init__(self):
        Gesture.__init__(self, "roomlist")
        self.imm_level = IMM_LEVELS["creator"]
     
    def execute(self, builder, args):
        if args:
            area_id = args[0]
        else:
            area_id = builder.env.area_id
        area = self.mud.get_area(area_id)
        if not area:
            return "Invalid area"
        display = Display()
        for room in area.rooms:
            display.append(DisplayLine(ljust(room.dbo_id, 20) + ljust(room.title, 20) + room.short_exits()))
        return display


class BuildError(Exception):
    def __init__(self, msg):
        self.msg = msg
        

def check_area(builder, area_id):
    if area_id == "immortal_citadel":
        raise BuildError("You cannot build in the immortal citadel")
    
    area = Gesture.mud.get_area(area_id)  #@UndefinedVariable
    if area.owner_id != builder.dbo_id:
        owner = Gesture.load_object(Player, area.owner_id)
        if owner.imm_level >= builder.imm_level:
            raise BuildError("You cannot build in " + owner.name + "'s area!")
    return area
    
def check_room(builder, room):
    return check_area(builder, room.area_id)
    
def find_room(builder, room_id, start_area):
    if not room_id:
        return None, None
    room_id = ":".join(room_id)
    if not ":" in room_id:
        room_id = "{0}:{1}".format(start_area, room_id) 
    try:
        area_id = room_id.split(":")[0]
        area = check_area(builder, area_id)
        room = area.get_room(room_id)
    except:
        raise BuildError("Invalid room id")
    return area, room
    
       
class BuildAction(Gesture):
    imm_level = IMM_LEVELS["creator"]
    
    def execute(self, builder, args):
        try:
            feedback = None
            room = builder.env
            area = check_room(builder, room)
            target = self.find_target(builder, args)
            builder.change_env(BUILD_ROOM)
            feedback = self.build(builder, room, area, target, args)         
        except BuildError as exp:  
            return exp.msg
        finally:
            if builder.env == BUILD_ROOM:
                if room.dbo_rev == -1:
                    builder.change_env(builder.home_room)
                else:
                    builder.change_env(room)
        if feedback:
            return feedback
        return builder.parse("look")
     
    
    def find_target(self, builder, args):
        key_data = builder.target_key_map.get(args)
        if key_data and len(key_data) == 1:
            return key_data[0]  

class DelRoom(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delroom")
        
    def execute(self, builder, args):
        if not args:
            return "Room id must be specified for delete"
        try:
            area, room = find_room(builder, args, builder.env.area_id)
        except BuildError as exp:
            return exp.msg

        if room.dbo_rev:
            confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to delete room " + room.short_desc(builder), "Confirm Delete", self.confirm_delete)
            confirm_dialog.area = area
            confirm_dialog.room = room
            return DialogMessage(confirm_dialog)
        else:
            return self.del_room(builder, area,  room)
            
    def confirm_delete(self, dialog):
        if dialog.data["response"] == "no":
            return
        return self.del_room(dialog.player, dialog.area, dialog.room)
        
    def del_room(self, builder, area, room):
        for my_exit in room.exits:
            other_room = my_exit.destination
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_room.exits.remove(other_exit)
                    self.save_object(other_room)
                    other_room.refresh()
        self.delete_object(room)
        area.rooms.remove(room)
        self.save_object(area)
        display = Display("Room " + room.dbo_id + " deleted")

        if builder.env == room:
            display.merge(builder.parse("home"))
        return display
        

class DirectionAction(BuildAction):
    def find_target(self, builder, args):
        direction = Direction.ref_map.get(args[0])
        if direction:
            return direction
        raise BuildError("No direction specified")
    
class Dig(DirectionAction):
    def __init__(self):
        Gesture.__init__(self, "dig")
   
    def build(self, builder, room, area, new_dir, args):
             
        if room.find_exit(new_dir):
            raise BuildError("This room already has a " + new_dir.desc + " exit.")
            
        desc =  area.name + " Room " + str(area.next_room_id)
        new_area, new_room = find_room(builder, args[1:], room.area_id)
        if new_room:
            if new_room.find_exit(new_dir.rev_dir):
                raise BuildError("The other room already has a {0} exit".format(new_dir.rev_key))
        else:
            new_room = Room(area.dbo_id + ":" + str(area.next_room_id), desc, desc)
            new_area = area
        
        this_exit = Exit(new_dir.key, new_room)
        room.exits.append(this_exit)
        room.refresh()
        self.save_object(room)
        
        other_exit = Exit(new_dir.rev_key, room)
        new_room.exits.append(other_exit)
        new_room.refresh()
        self.save_object(new_room)
        
        new_area.rooms.append(new_room)
        area.next_room_id = area.next_room_id + 1
        builder.change_env(new_room)
        self.save_object(area)

    
class UnDig(DirectionAction):
    remove_other_exit = True
    remove_other_room = True
    
    def __init__(self):
        Gesture.__init__(self, "undig")
        
    def build(self, builder, room, area, target_dir, args):
  
        my_exit = room.find_exit(target_dir)
        other_room = my_exit.destination
       
        room.exits.remove(my_exit)
        room.refresh()
        self.save_object(room)
        
        if not self.remove_other_exit:
            return
        
        other_exit = other_room.find_exit(target_dir.rev_dir)
        
        if not other_exit:
            return
            
        other_room.exits.remove(other_exit)
        if self.remove_other_room and not other_room.dbo_rev and not other_room.exits:
            other_room.dbo_rev = -1
            self.delete_object(other_room)
            area.rooms.remove(other_room)
            self.save_object(area)
        else:
            self.save_object(other_room)
            other_room.refresh()
            

class FTH(UnDig):
    def __init__(self):
        Gesture.__init__(self, "fth")
        self.remove_other_room = False

                
class BackFill(UnDig):
    def __init__(self):
        Gesture.__init__(self, "backfill")
        self.remove_other_exit = False
                
                        
class SetDesc(BuildAction):
    def __init__(self):
        Gesture.__init__(self, ("rdesc",  "setdesc"))
    
    def create_message(self, builder, verb, target, command):
        try:
            check_room(builder, builder.env)
            if not target:
                return "Set description to what?"
            builder.env.desc = command.partition(" ")[2]
            self.save_object(builder.env, True)
        except BuildError as exp:
            return exp.msg
        return builder.parse("look")
 
        
class SetTitle(BuildAction):
    def __init__(self):
        Gesture.__init__(self, ("rname", "settitle"))
    
    def create_message(self, builder, verb, target, command):
        try:
            check_room(builder, builder.env)
            if not target:
                return "Set title to what?"
            builder.env.title = command.partition(" ")[2]
            self.save_object(builder.env, True)
        except BuildError as exp:
            return exp.msg
        return builder.parse("look")
        

            