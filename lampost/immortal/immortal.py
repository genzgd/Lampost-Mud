'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from lampost.action.action import Action
from lampost.client.dialog import Dialog, DIALOG_TYPE_CONFIRM
from lampost.comm.broadcast import SingleBroadcast
from lampost.context.resource import requires
from lampost.dto.display import Display, DisplayLine
from lampost.dto.rootdto import RootDTO
from lampost.env.room import Room
from lampost.mud.area import Area
from lampost.player.player import Player
from lampost.util.lmutil import ljust, find_extra, patch_object, PatchError

import string

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class ListCommands(Action):
    def __init__(self):
        Action.__init__(self, "cmds")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, **ignored):
        soul_actions = [action for action in source.soul if action.imm_level]
        verb_lists = ["/".join([" ".join(list(verb)) for verb in action.verbs]) for action in soul_actions]
        return ", ".join(sorted(verb_lists))

class AllPlayers(Action):
    def __init__(self):
        Action.__init__(self, "allplayers")
        self.imm_level = IMM_LEVELS["admin"]
        
    def execute(self, **ignored):
        player_keys = self.datastore.fetch_set_keys("players")
        return " ".join([player.split(":")[1] for player in player_keys])

@requires('sm')
class GotoPlayer(Action):
    def __init__(self):
        Action.__init__(self, ("goto player", "gplayer"))
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not args:
            return "player name required"
        session = self.sm.player_session_map.get(args[0]) #@UndefinedVariable
        if not session:
            return "Cannot find " + args[0]
        source.change_env(session.player.env)
        return source.parse("look")
        
class PatchTarget(Action):
    def __init__(self):
        Action.__init__(self, "patch")
        self.imm_level = IMM_LEVELS["admin"]
        
    def execute(self, source, verb, args, command, **ignored):
        try:
            split_ix = args.index(":")
            target_id = args[:split_ix]
            prop = args[split_ix + 1]
            new_value =  find_extra(verb, split_ix + 2, command)
        except (ValueError, IndexError):
            return "Syntax -- 'patch [target] [:] [prop_name] [new_value]'"
        target_list = list(source.matching_targets(target_id, "__dict__"))
        if not target_list:
            return "No matching target"
        if len(target_list) > 1:
            return "Multiple matching targets"
        if not new_value:
            return "New value required"
        if new_value == "None":
            new_value = None     
        if prop == "imm_level":
            try:
                if source.imm_level < int(new_value):
                    return "Umm, no."
            except ValueError:
                return "Invalid value"    
        try:
            patch_object(target_list[0][0], prop, new_value)
        except PatchError as exp:
            return exp.message
        return "Object successfully patched"
        
class PatchDB(Action):
    def __init__(self):
        Action.__init__(self, "patchdb")
        self.imm_level = IMM_LEVELS["admin"]
        
    def execute(self, source, verb, args, command, **ignored):
        if len(args) == 0:
            return "Type required."
        obj_type = args[0]
        if len(args) == 1:
            return "Object id required."
        obj_id = args[1]
        if len(args) == 2:
            return "Property name required."
        prop = args[2]
        new_value = find_extra(verb, 3, command)
        if not new_value:
            return "Value required."
        if new_value == "None":
            new_value = None
        if prop == "imm_level":
            try:
                if source.imm_level < int(new_value):
                    return "Umm, no."
            except ValueError:
                return "Invalid value"   
        key = ":".join([obj_type, obj_id])
        if obj_type == "player":
            obj = self.load_object(Player, obj_id)
        else:
            obj = self.datastore.load_cached(key)
        if not obj:
            return "Object not found"
        try:
            patch_object(obj, prop, new_value)
        except PatchError as exp:
            return exp.message
            
        self.save_object(obj)
        return "Object " + key + " patched"
 
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
    room = Action.mud.find_room(room_id) #@UndefinedVariable
    if not room:
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
        source.unregister_type(args[0], source.display_line)

@requires('sm')
class DeletePlayer(Action):
    def __init__(self):
        Action.__init__(self, "delete player")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, args, **ignored):
        if not args:
            return "Player name not specified"
        player_id = args[0].lower()
        if self.sm.player_session_map.get(player_id): #@UndefinedVariable
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
        display = Display(" ")
        for line in target.describe():
            display.append(DisplayLine(line))
        return display


class CreateArea(Action):
    def __init__(self):
        Action.__init__(self, "create area")
        self.imm_level = IMM_LEVELS["creator"]
    
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
                