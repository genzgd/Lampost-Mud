'''
Created on Apr 8, 2012

@author: Geoffrey
'''
from immortal import IMM_LEVELS
from movement import Direction
from player import Player
from room import Room, Exit
from lmutil import ljust
from dto.display import Display, DisplayLine
from dialog import Dialog, DIALOG_TYPE_CONFIRM
from action import Action

BUILD_ROOM = Room("buildroom")

class BuildMode(Action):
    def __init__(self):
        Action.__init__(self, "buildmode")
        
    def execute(self, source, **ignored):
        current = getattr(source, "buildmode", False)
        source.buildmode = not current
        return "Build Mode is {0}".format("On" if source.buildmode else "Off")


class RoomList(Action):
    def __init__(self):
        Action.__init__(self, "roomlist")
     
    def execute(self, source, args, **ignored):
        if args:
            area_id = args[0]
        else:
            area_id = source.env.area_id
        area = self.mud.get_area(area_id)
        if not area:
            return "Invalid area"
        display = Display()
        for room in area.sorted_rooms:
            display.append(DisplayLine(ljust(room.dbo_id, 20) + ljust(room.title, 20) + room.short_exits()))
        return display


class MobList(Action):
    def __init__(self):
        Action.__init__(self, "moblist")
     
    def execute(self, source, args, **ignored):
        if args:
            area_id = args[0]
        else:
            area_id = source.env.area_id
        area = self.mud.get_area(area_id)
        if not area:
            return "Invalid area"
        if not area.mobiles:
            return "No mobiles defined"
        display = Display()
        for mobile in area.mobiles:
            display.append(DisplayLine(ljust(mobile.dbo_id, 20) + ljust(mobile.title, 20) + mobile.level))
        return display


class BuildError(Exception):
    def __init__(self, msg):
        self.msg = msg
        

def check_area(builder, area_id):
    if area_id == "immortal_citadel" and builder.imm_level < IMM_LEVELS["supreme"]:
        raise BuildError("You cannot build in the immortal citadel")
    
    area = Action.mud.get_area(area_id)  #@UndefinedVariable
    if area.owner_id != builder.dbo_id:
        owner = Action.load_object(Player, area.owner_id)
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
    
       
class BuildAction(Action):
    imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, args, **ignored):
        try:
            feedback = None
            room = source.env
            area = check_room(source, room)
            target = self.find_target(source, args)
            source.change_env(BUILD_ROOM)
            feedback = self.build(source, room, area, target, args)         
        except BuildError as exp:  
            return exp.msg
        finally:
            if source.env == BUILD_ROOM:
                if room.dbo_rev == -1:
                    source.change_env(source.home_room)
                else:
                    source.change_env(room)
        if feedback:
            return feedback
        return source.parse("look")
         
    def find_target(self, builder, args):
        key_data = builder.target_key_map.get(args)
        if key_data and len(key_data) == 1:
            return key_data[0]  

class ResetRoom(Action):
    def __init__(self):
        Action.__init__(self, "reset")
    
    def execute(self, source, args, **ignored):
        area = Action.mud.get_area(source.env.area_id) #@UndefinedVariable
        source.env.reset(area)
        return "Room reset"

class DelRoom(Action):
    def __init__(self):
        Action.__init__(self, "delroom")
        
    def execute(self, source, args, **ignored):
        if not args:
            return "Room id must be specified for delete"
        try:
            area, room = find_room(source, args, source.env.area_id)
        except BuildError as exp:
            return exp.msg

        if room.dbo_rev:
            confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to delete room " + room.title, "Confirm Delete", self.confirm_delete)
            confirm_dialog.area = area
            confirm_dialog.room = room
            return confirm_dialog
        else:
            return self.del_room(source, area,  room)
            
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
        direction = Direction.find_dir(args[0])
        if direction:
            return direction
        raise BuildError("No direction specified")
    
class Dig(DirectionAction):
    def __init__(self):
        Action.__init__(self, "dig")
   
    def build(self, builder, room, area, new_dir, args):
             
        if room.find_exit(new_dir):
            raise BuildError("This room already has a " + new_dir.desc + " exit.")
            
        desc = area.name + " Room " + str(area.next_room_id)
        new_area, new_room = find_room(builder, args[1:], room.area_id)
        if new_room:
            if new_room.find_exit(new_dir.rev_dir):
                raise BuildError("The other room already has a {0} exit".format(new_dir.rev_key))
        else:
            new_room = Room(area.dbo_id + ":" + str(area.next_room_id), desc, desc)
            new_area = area
            new_area.rooms.append(new_room)
        
        this_exit = Exit(new_dir, new_room)
        room.exits.append(this_exit)
        room.refresh()
        self.save_object(room)
        
        other_exit = Exit(new_dir.rev_dir, room)
        new_room.exits.append(other_exit)
        new_room.refresh()
        self.save_object(new_room)
        
        area.next_room_id = area.next_room_id + 1
        self.save_object(area)

    
class UnDig(DirectionAction):
    remove_other_exit = True
    remove_other_room = True
    
    def __init__(self):
        Action.__init__(self, "undig")
        
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
        Action.__init__(self, "fth")
        self.remove_other_room = False

                
class BackFill(UnDig):
    def __init__(self):
        Action.__init__(self, "backfill")
        self.remove_other_exit = False
                                      
class SetDesc(Action):
    def __init__(self):
        Action.__init__(self, ("rdesc",  "setdesc"))
    
    def execute(self, source, args, command, **ignored):
        try:
            if not args:
                return "Set description to what?"
            check_room(source, source.env)
            source.env.desc = command.partition(" ")[2]
            self.save_object(source.env, True)
        except BuildError as exp:
            return exp.msg
        return source.parse("look")
 
        
class SetTitle(Action):
    def __init__(self):
        Action.__init__(self, ("rname", "settitle"))
    
    def execute(self, source, args, command, **ignored):
        try:
            check_room(source, source.env)
            if not args:
                return "Set title to what?"
            source.env.title = command.partition(" ")[2]
            self.save_object(source.env, True)
        except BuildError as exp:
            return exp.msg
        return source.parse("look")
            