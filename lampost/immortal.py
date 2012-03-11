'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from action import Gesture
from player import Player
from dialog import Dialog, DIALOG_TYPE_CONFIRM
from context import Context
from dto.rootdto import RootDTO
from dto.display import Display
from message import LMessage, DialogMessage

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class CreatePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create player")
        self.imm_level = IMM_LEVELS["supreme"]
        
    def create_message(self, source, verb, target, command):
        if not len(target):
            return "Name not specified"
        player = Player(target[0])
        if self.load_object(player):
            return "That player already exists"
        if len(target) > 1:
            imm_level = IMM_LEVELS.get(target[1])
            if not imm_level:
                return "Invalid Immortal Level"
        else:
            imm_level = 0
        player.imm_level = imm_level
        self.save_object(player)
        return LMessage(source, None, None)
        
                
class DeletePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "delete player")
        self.imm_level = IMM_LEVELS["supreme"]
        
    def create_message(self, source, verb, target, command):
        if not len(target):
            return "Name not specified"
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
        if self.load_object(todie):
            self.delete_object(todie)
            return Display(dialog.player_id + " deleted")
        return Display("Player " + dialog.player_id + " does not exist.")
        