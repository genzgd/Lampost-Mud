'''
Created on Apr 8, 2012

@author: Geoffrey
'''
from action import Gesture
from immortal import IMM_LEVELS
from movement import Direction
from player import Player
from room import Room, Exit

BUILD_ROOM = Room("buildroom")

class Dig(Gesture):
    def __init__(self):
        Gesture.__init__(self, "dig")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        try:
            new_dir = Direction.ref_map[target[0]]
            rev_dir = new_dir.rev
        except:
            return "Invalid direction"
        
        curr = source.env
        area_id = curr.area_id
        
        if area_id == "immortal_citadel":
            return "You cannot dig in the immortal citadel"
        
        area = self.mud.get_area(area_id)
        if area.owner_id != source.dbo_id:
            owner = self.load_object(Player, area.owner_id)
            if owner.imm_level >= source.imm_level:
                return "You cannot dig in " + owner.name + "'s area!"
            
        for ext in curr.exits:
            if ext.dir_name == new_dir.key:
                return "This room already has a " + new_dir.desc + " exit."
            
        source.change_env(BUILD_ROOM)
        
        desc =  area.name + " Room " + str(area.next_room_id)
        room = Room(area_id + ":" + str(area.next_room_id), desc, desc)
        
        this_exit = Exit(new_dir.key, room)
        curr.exits.append(this_exit)
        self.save_object(curr)
        
        other_exit = Exit(rev_dir, curr)
        room.exits.append(other_exit)
        self.save_object(room)
        
        area.rooms.append(room)
        area.next_room_id = area.next_room_id + 1
        self.save_object(area)
        
        source.change_env(room)
        return source.parse("l")
       
        
        
        
            
        
    
