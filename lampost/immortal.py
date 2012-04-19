'''
Created on Mar 4, 2012

@author: Geoffrey
'''
import string

from action import Action
from player import Player
from dialog import Dialog, DIALOG_TYPE_CONFIRM
from context import Context
from dto.rootdto import RootDTO
from dto.display import Display, DisplayLine
from area import Area
from room import Room
from lmutil import ljust
from broadcast import SingleBroadcast

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class ListCommands(Action):
    def __init__(self):
        Action.__init__(self, "cmds")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, **ignored):
        soul_actions = [action for action in source.soul if action.imm_level]
        verb_lists = ["/".join([" ".join(list(verb)) for verb in action.verbs]) for action in soul_actions]
        return ", ".join(sorted(verb_lists))
 
class AreaList(Action):
    def __init__(self):
        Action.__init__(self, ("arealist", "alist"))
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, **ignored):
        display = Display()
        for area in sorted(self.mud.area_map.itervalues()):
            display.append(DisplayLine(ljust(area.name, 20) + ljust(area.owner_id, 20) + str(len(area.rooms)) + " rooms"))
        return display


class SetHome(Action):
    def __init__(self):
        Action.__init__(self, "sethome")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, **ignored):
        source.home_room = source.env.dbo_id

def goto_room(player, room_id):
        if not ":" in room_id:
            room_id = ":".join([player.env.area_id, room_id])
        area_id = room_id.split(":")[0]

        try:
            area = Action.mud.get_area(area_id) #@UndefinedVariable
            room = area.get_room(room_id)
            if not room:
                return "No such room in " + area.name
        except:
            return "Cannot find room " + room_id
        player.change_env(room)
        return player.parse("look")

    
class GotoRoom(Action):
    def __init__(self):
        Action.__init__(self, "goto room")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        return goto_room(source, ":".join(args))
        
  
class Zap(Action):
    def __init__(self):
        Action.__init__(self, "zap", "damage")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target_method, target, **ignored):
        target_method(1000000)
        return SingleBroadcast(source, "An immortal recklessly wields power.")
    
        
class GoHome(GotoRoom):
    def __init__(self):
        Action.__init__(self, "home")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, **ignored):
        return goto_room(source, source.home_room)


class CreatePlayer(Action):
    def __init__(self):
        Action.__init__(self, "create player")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not len(args):
            return "Name not specified"
            
        if self.load_object(Player, args[0]):
            return "That player already exists"
        player = Player(args[0])
        if len(args) > 1:
            imm_level = IMM_LEVELS.get(args[1])
            if not imm_level:
                return "Invalid Immortal Level"
            title = args[1]
            if imm_level >= source.imm_level:
                return "Cannot create player with a higher level or the same level as yourself"
            player.imm_level = imm_level
        else:
            title = "player"
            
        self.save_object(player)    
        return title + " " + player.name + " created."
    
        
class RegisterDisplay(Action):
    def __init__(self):
        Action.__init__(self, "register display")
        self.imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, args, **ignored):
        if not args:
            return "No event specified"
        source.register(args[0], source.display_line)
        

class UnregisterDisplay(Action):
    def __init__(self):
        Action.__init__(self, "unregister display")
        self.imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, args, **ignored):
        source.unregister(args[0], source.display_line)
                   
class DeletePlayer(Action):
    def __init__(self):
        Action.__init__(self, "delete player")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not args:
            return "Player name not specified"
        player_id = args[0].lower()
        if Context.instance.sm.player_session_map.get(player_id): #@UndefinedVariable
            return "Player " + player_id + " logged in, cannot delete."
        todie = self.load_object(Player, player_id)
        if todie:
            if todie.imm_level >= source.imm_level:
                return "Cannot delete player of same or lower level."
            confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to permanently remove " + todie.name, "Confirm Delete", self.finish_delete)
            confirm_dialog.player_id = player_id
            return confirm_dialog
        return "Player " + player_id + " does not exist."
        
    def finish_delete(self, dialog):
        if dialog.data["response"] == "no":
            return RootDTO(silent=True)
        todie = self.load_object(Player, dialog.player_id)
        if todie:      
            self.delete_object(todie)
            return Display(dialog.player_id + " deleted.")


class Describe(Action):
    def __init__(self):
        Action.__init__(self, "describe")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not args:
            target = source.env
        else:
            target = self.datastore.load_cached(args[0])
        if not target:
            return "No object with that key found"
        display = Display("&nbsp")
        for line in target.describe():
            display.append(DisplayLine(line))
        return display


class CreateArea(Action):
    def __init__(self):
        Action.__init__(self, "create area")
        self.imm_level = IMM_LEVELS["admin"]
    
    def execute(self, source, args, **ignored):
        if not args:
            return "Area name not specified"
        area_id = "_".join(args).lower()
        if self.load_object(Area, area_id):
            return "That area already exists"
        area = Area(area_id)
        area_name = " ".join(args)
        area.name = string.capwords(area_name)
        room = Room(area_id + ":0", "Area " + area.name + " Start", "The Initial Room in " + area.name + " Area")
        area.rooms.append(room)
        area.owner_id = source.dbo_id
        self.create_object(area)
        self.mud.add_area(area)
        source.parse("goto room " + room.dbo_id)


class DeleteArea(Action):
    def __init__(self):
        Action.__init__(self, "delete area")
        self.imm_level = IMM_LEVELS["admin"]
    
    def execute(self, source, args, **ignored):
        if not args:
            return "Area name not specified"
        area_id = args[0].lower()
        confirm_dialog = Dialog(DIALOG_TYPE_CONFIRM, "Are you sure you want to permanently remove area: " + area_id, "Confirm Delete", self.finish_delete)
        confirm_dialog.area_id = area_id
        return confirm_dialog
         
    def finish_delete(self, dialog):
        if dialog.data["response"] == "no":
            return
        area = self.load_object(Area, dialog.area_id)
        if area:
            area.detach()
            self.delete_object(area)
            del self.mud.area_map[dialog.area_id]
            return dialog.area_id + " deleted."
        else:
            return "Area " + dialog.area_id + " does not exist."

class GoToArea(Action):
    def __init__(self):
        Action.__init__(self, "goto area")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not args:
            return "Area name not specified"
        area = self.mud.get_area(" ".join(args))
        if not area:
            return "Area does not exist"
        if not area.rooms:
            return "Area has no rooms!"
        dest = area.first_room
        source.change_env(dest)
        return source.parse("look")

    
class Citadel(GoToArea):
    def __init__(self):
        Action.__init__(self, "citadel")
        self.imm_level = IMM_LEVELS["creator"]
     
    def execute(self, source, **ignored):
        return GoToArea.execute(self, source, ("immortal", "citadel"))
                