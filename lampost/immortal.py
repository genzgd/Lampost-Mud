'''
Created on Mar 4, 2012

@author: Geoffrey
'''
import string

from action import Gesture
from player import Player
from dialog import Dialog, DIALOG_TYPE_CONFIRM
from context import Context
from dto.rootdto import RootDTO
from dto.display import Display, DisplayLine
from message import DialogMessage, CLASS_MOVEMENT, LMessage, CLASS_SENSE_EXAMINE
from area import Area
from room import Room
from lmutil import ljust

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class ListCommands(Gesture):
    def __init__(self):
        Gesture.__init__(self, "cmds")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        soul_actions = [action for action in source.soul if action.imm_level]
        verb_lists = ["/".join([" ".join(list(verb)) for verb in action.verbs]) for action in soul_actions]
        return ", ".join(sorted(verb_lists))
 
class AreaList(Gesture):
    def __init__(self):
        Gesture.__init__(self, "arealist")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        display = Display()
        for area in sorted(self.mud.area_map.itervalues()):
            display.append(DisplayLine(ljust(area.name, 20) + ljust(area.owner_id, 20) + str(len(area.rooms)) + " rooms"))
        return display


class SetHome(Gesture):
    def __init__(self):
        Gesture.__init__(self, "sethome")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        source.home_room = source.env.dbo_id

    
class GotoRoom(Gesture):
    def __init__(self):
        Gesture.__init__(self, "goto room")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, player, target):
        return self.goto_room(player, ":".join(target))
        
    def goto_room(self, player, room_id):
        try:
            area_id = room_id.split(":")[0]
            area = self.mud.get_area(area_id)
            room = area.get_room(room_id)
            if not room:
                return "No such room in " + area.name
        except:
            return "Cannot find room " + room_id
        player.change_env(room)
        return player.parse("look")
   
        
class GoHome(GotoRoom):
    def __init__(self):
        Gesture.__init__(self, "home")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, player, target):
        return self.goto_room(player, player.home_room)


class CreatePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create player")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        if not len(target):
            return "Name not specified"
        if self.load_object(Player, target[0]):
            return "That player already exists"
        if len(target) > 1:
            imm_level = IMM_LEVELS.get(target[1])
            if not imm_level:
                return "Invalid Immortal Level"
            title = target[1]
            if imm_level >= source.imm_level:
                return "Cannot create player with a higher level or the same level as yourself"
        else:
            imm_level = 0
            title = "player"
        player = Player(target[0])
        player.imm_level = imm_level
        player.room_id = None
        self.save_object(player)
        
        return title + " " + player.name + " created."
    
        
class RegisterDisplay(Gesture):
    def __init__(self):
        Gesture.__init__(self, "register display")
        self.imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, target):
        if not len(target):
            return "No event specified"
        source.register(target[0], source.display_line)
        

class UnregisterDisplay(Gesture):
    def __init__(self):
        Gesture.__init__(self, "unregister display")
        self.imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, target):
        for reg in source.registrations:
            if reg.event_type == target[0] and reg.callback == source.display_line:
                reg.detach()
        
                   
class DeletePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delete player")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        if not len(target):
            return "Player name not specified"
        player_id = target[0].lower()
        if Context.instance.sm.player_session_map.get(player_id): #@UndefinedVariable
            return "Player " + player_id + " logged in, cannot delete."
        todie = self.load_object(Player, player_id)
        if todie:
            if todie.imm_level >= source.imm_level:
                return "Cannot delete player of same or lower level."
            confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to permanently remove " + todie.name, "Confirm Delete", self.finish_delete)
            confirm_dialog.player_id = player_id
            return DialogMessage(confirm_dialog)
        return "Player " + player_id + " does not exist."
        
    def finish_delete(self, dialog):
        if dialog.data["response"] == "no":
            return RootDTO(silent=True)
        todie = self.load_object(Player, dialog.player_id)
        if todie:      
            self.delete_object(todie)
            return Display(dialog.player_id + " deleted.")


class Describe(Gesture):
    def __init__(self):
        Gesture.__init__(self, "describe")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        if not len(target):
            target = source.env
        else:
            target = self.datastore.load_cached(target[0])
        if not target:
            return "No object with that key found"
        display = Display("&nbsp")
        for line in target.describe():
            display.append(DisplayLine(line))
        return display


class CreateArea(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create area")
        self.imm_level = IMM_LEVELS["admin"]
    
    def execute(self, source, target):
        if not len(target):
            return "Area name not specified"
        area_id = "_".join(target).lower()
        if self.load_object(Area, area_id):
            return "That area already exists"
        area = Area(area_id)
        area_name = " ".join(target)
        area.name = string.capwords(area_name)
        area.next_room_id = 1
        room = Room(area_id + ":0", "Area " + area.name + " Start", "The Initial Room in " + area.name + " Area")
        area.rooms.append(room)
        area.owner_id = source.dbo_id
        self.save_object(area)
        self.mud.add_area(area)
        source.parse("goto room " + room.dbo_id)


class DeleteArea(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delete area")
        self.imm_level = IMM_LEVELS["admin"]
    
    def execute(self, source, target):
        if not len(target):
            return "Area name not specified"
        area_id = target[0].lower()
        confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to permanently remove area: " + area_id, "Confirm Delete", self.finish_delete)
        confirm_dialog.area_id = area_id
        return DialogMessage(confirm_dialog)
         
    def finish_delete(self, dialog):
        if dialog.data["response"] == "no":
            return RootDTO(silent=True)
        area = self.load_object(Area, dialog.area_id)
        if area:
            self.delete_object(area)
            del self.mud.area_map[dialog.area_id]
            return Display(dialog.area_id + " deleted.")
        return Display("Area " + dialog.area_id + " does not exist.")


class GoToArea(Gesture):
    def __init__(self):
        Gesture.__init__(self, "goto area")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target):
        if not len(target):
            return "Area name not specified"
        area = self.mud.get_area(" ".join(target))
        if not area:
            return "Area does not exist"
        dest = area.rooms[0]
        source.receive(LMessage(self, CLASS_MOVEMENT, dest))
        return dest.receive(LMessage(source, CLASS_SENSE_EXAMINE))

    
class Citadel(GoToArea):
    def __init__(self):
        Gesture.__init__(self, "citadel")
        self.imm_level = IMM_LEVELS["creator"]
     
    def execute(self, source, target):
        return GoToArea.execute(self, source, ("immortal", "citadel"))

        
    
                