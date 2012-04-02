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
from dto.display import Display
from message import DialogMessage, CLASS_MOVEMENT, LMessage, CLASS_SENSE_EXAMINE
from area import Area
from room import Room

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class CreatePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create player")
        self.imm_level = IMM_LEVELS["supreme"]
        
    def execute(self, source, target):
        if not len(target):
            return "Name not specified"
        player = Player(target[0])
        if self.hydrate_object(player):
            return "That player already exists"
        if len(target) > 1:
            imm_level = IMM_LEVELS.get(target[1])
            if not imm_level:
                return "Invalid Immortal Level"
            if imm_level > source.imm_level:
                return "Cannot create player with a higher level than yourself"
        else:
            imm_level = 0
        player.imm_level = imm_level
        player.room_id = None
        self.save_object(player)
        
                
class DeletePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delete player")
        self.imm_level = IMM_LEVELS["supreme"]
        
    def execute(self, source, target):
        if not len(target):
            return "Player name not specified"
        player_id = target[0].lower()
        if Context.instance.sm.player_session_map.get(player_id): #@UndefinedVariable
            return "Player " + player_id + " logged in, cannot delete."
        confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to permanently remove " + player_id, "Confirm Delete", self.finish_delete)
        confirm_dialog.player_id = player_id
        return DialogMessage(confirm_dialog)
        
    def finish_delete(self, dialog):
        if dialog.data["response"] == "no":
            return RootDTO(silent=True)
        todie = Player(dialog.player_id)
        if self.hydrate_object(todie):
            self.delete_object(todie)
            return Display(dialog.player_id + " deleted.")
        return Display("Player " + dialog.player_id + " does not exist.")


class CreateArea(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create area")
        self.imm_level = IMM_LEVELS["supreme"]
    
    def execute(self, source, target):
        if not len(target):
            return "Area name not specified"
        area_id = "_".join(target).lower()
        area = Area(area_id)
        if self.hydrate_object(area):
            return "That area already exists"
        area_name = " ".join(target)
        area.name = string.capwords(area_name)
        room = Room(area_id + ":0", "The Beginning", "The Initial Room in " + area.name + " Area")
        area.rooms.append(room)
        self.save_object(area)
        self.mud.add_area(area)


class DeleteArea(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delete area")
        self.imm_level = IMM_LEVELS["supreme"]
    
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
        area = Area(dialog.area_id)
        if self.hydrate_object(area):
            self.delete_object(area)
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

        
    
                