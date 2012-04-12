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

BUILD_ROOM = Room("buildroom")


class RoomList(Gesture):
    def __init__(self):
        Gesture.__init__(self, "roomlist")
        self.imm_level = IMM_LEVELS["creator"]
     
    def execute(self, builder, args):
        if len(args) == 1:
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
        
        
class BuildAction(Gesture):
    imm_level = IMM_LEVELS["creator"]
    
    def execute(self, builder, args):
        try:
            feedback = None
            room = builder.env
            area = self.check_area(builder, room)
            target = self.find_target(builder, args)
            builder.change_env(BUILD_ROOM)
            feedback = self.build(builder, room, area, target, args)         
        except BuildError as exp:  
            return exp.msg
        finally:
            if builder.env == BUILD_ROOM:
                builder.change_env(room)
        if feedback:
            return feedback
        return builder.parse("look")
     
    def check_area(self, builder, room):
        area_id = room.area_id
        
        if area_id == "immortal_citadel":
            raise BuildError("You cannot dig in the immortal citadel")
        
        area = self.mud.get_area(area_id)
        if area.owner_id != builder.dbo_id:
            owner = self.load_object(Player, area.owner_id)
            if owner.imm_level >= builder.imm_level:
                raise BuildError("You cannot dig in " + owner.name + "'s area!")
        return area
    
    def find_target(self, builder, args):
        key_data = builder.target_key_map.get(args)
        if key_data and len(key_data) == 1:
            return key_data[0]  


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
        new_room = Room(area.dbo_id + ":" + str(area.next_room_id), desc, desc)
        
        this_exit = Exit(new_dir.key, new_room)
        room.exits.append(this_exit)
        self.save_object(room)
        
        other_exit = Exit(new_dir.rev_key, room)
        new_room.exits.append(other_exit)
        self.save_object(new_room)
        
        area.rooms.append(new_room)
        area.next_room_id = area.next_room_id + 1
        builder.change_env(new_room)
        self.save_object(area)

    
class UnDig(DirectionAction):
    def __init__(self):
        Gesture.__init__(self, "undig")
        
    def build(self, builder, room, area, target_dir, args):
  
        my_exit = room.find_exit(target_dir)
        other_room = my_exit.destination
       
        room.exits.remove(my_exit)
        self.save_object(room)
        
        other_exit = other_room.find_exit(target_dir.rev_dir)
        
        if other_exit:
            other_room.exits.remove(other_exit)
        
            if not other_room.rev and not other_room.exits:
                self.delete_object(other_room)
                area.rooms.remove(other_room)
                self.save_object(area)
            else:
                self.save_object(other_room)
      
                
class SetDesc(BuildAction):
    def __init__(self):
        Gesture.__init__(self, "setdesc")
    
    def create_message(self, builder, verb, target, command):
        try:
            self.check_area(builder, builder.env)
            if not target:
                return "Set description to what?"
            builder.env.desc = command.partition(" ")[2]
            self.save_object(builder.env)
        except BuildError as exp:
            return exp.msg
        return builder.parse("look")
 
        
class SetTitle(BuildAction):
    def __init__(self):
        Gesture.__init__(self, "settitle")
    
    def create_message(self, builder, verb, target, command):
        try:
            self.check_area(builder, builder.env)
            if not target:
                return "Set title to what?"
            builder.env.title = command.partition(" ")[2]
            self.save_object(builder.env)
        except BuildError as exp:
            return exp.msg
        return builder.parse("look")
        
        
        
            
    
                

            