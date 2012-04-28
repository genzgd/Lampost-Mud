'''
Created on Apr 8, 2012

@author: Geoffrey
'''
from immortal import IMM_LEVELS
from lampost.env.movement import Direction
from lampost.player.player import Player
from lampost.env.room import Room, Exit
from lampost.util.lmutil import ljust, find_extra, find_extra_prep
from lampost.dto.display import Display, DisplayLine
from lampost.client.dialog import Dialog, DIALOG_TYPE_CONFIRM
from lampost.action.action import Action
from lampost.mobile.mobile import MobileTemplate, MobileReset
from lampost.mud.area import Area
from lampost.model.item import BaseItem

BUILD_ROOM = Room("buildroom")

class BuildMode(Action):
    imm_level = IMM_LEVELS["creator"]
    
    def __init__(self):
        Action.__init__(self, "buildmode")
        
    def execute(self, source, **ignored):
        current = getattr(source, "build_mode", False)
        source.build_mode = not current
        return "Build Mode is {0}".format("On" if source.build_mode else "Off")


class RoomList(Action):
    imm_level = IMM_LEVELS["creator"]
    
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
    imm_level = IMM_LEVELS["creator"]
    
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
            display.append(DisplayLine(ljust(mobile.dbo_id, 20) + ljust(mobile.title, 20) + unicode(mobile.level)))
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

class DeleteArea(Action):
    def __init__(self):
        Action.__init__(self, "delete area")
        self.imm_level = IMM_LEVELS["creator"]
    
    def execute(self, source, args, **ignored):
        if not args:
            return "Area name not specified"
        area_id = args[0].lower()
        try:
            check_area(source, area_id)
        except BuildError as exp:
            return exp.msg
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
 
class CreateMob(Action):
    imm_level = IMM_LEVELS["creator"]
    
    def __init__(self):
        Action.__init__(self, "areamob")
        
    def execute(self, source, args, command, **ignored):
        area_id = source.env.area_id;
        if not args:
            return "mob id required"
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg;
            
        mobile_id = ":".join([area_id, args[0]])
        if area.get_mobile(mobile_id):
            return mobile_id + " already exists in this area"
        
        title = command.partition(args[0])[2][1:]
        if not title:
            title = area.name + " " + args[0]
        template = MobileTemplate(mobile_id, title)
        self.save_object(template)
        area.mobiles.append(template)
        self.save_object(area)

        
class EditAreaMob(Action):
    imm_level = IMM_LEVELS["creator"]
    
    def __init__(self):
        Action.__init__(self, ("delareamob", "mlevel", "mname", "mdesc"))
        
    def execute(self, source, verb, args, command, **ignored):
        area_id = source.env.area_id;
        if not args:
            return "mob id required"
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg;
            
        mob_template = area.get_mobile(args[0])
        if not mob_template:
            return "Monster does not exist in this area"
            
        if verb[0] == "delareamob":
            mobile_resets = list(area.find_mobile_resets(mob_template.mobile_id))
            if mobile_resets:
                if len(args) < 2 or args[1] != "force":
                    return "Mobile is used in rooms.  Use 'force' option to remove from rooms"
                for room, mobile_reset in mobile_resets:
                    room.mobile_resets.remove(mobile_reset)
                    self.save_object(room, True)
            
            area.mobiles.remove(mob_template)
            self.save_object(area)
            return mob_template.mobile_id + " deleted."
            
        if len(args) < 2:
            return "Value required"
            
        if verb[0] == "mlevel":
            try:
                mob_template.level = int(args[1])
            except TypeError:
                return "Invalid level"
        
        else:
            value = " ".join(command.split(" ")[2:])
            if verb[0] == "mdesc":
                mob_template.desc = value
            elif verb[0] == "mname":
                mob_template.title = value
        self.save_object(mob_template)
        return mob_template.mobile_id + " updated"
            
                
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
                    Action.mud.start_player(source) #@UndefinedVariable
                else:
                    source.change_env(room)
        if feedback:
            return feedback
        return source.parse("look")
         
    def find_target(self, builder, args):
        key_data = builder.target_key_map.get(args)
        if key_data and len(key_data) == 1:
            return key_data[0]
            
class AddExtra(Action):
    def __init__(self):
        Action.__init__(self, "addextra")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, verb, args, command, **ignored):
        try:
            check_room(source, source.env)
        except BuildError as exp:
            return exp.msg
            
        if not args:
            return "Set title to what?"
        extra = BaseItem()
        extra.desc = find_extra(verb, 1, command)
        if not extra.desc:
            return "Description required"
        extra.title = args[0]
        extra.on_loaded()
        source.clear_all()
        source.env.extras.append(extra)
        self.save_object(source.env, True)
        source.refresh_all() 
        return extra.title + " added to room."
        
        
class DelExtra(Action):
    def __init__(self):
        Action.__init__(self, "delextra", "examine")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, target, **ignored):
        try:
            check_room(source, source.env)
        except BuildError as exp:
            return exp.msg
        if not target in source.env.extras:
            return target.target_id + " not part of room."
        source.clear_all()
        source.env.extras.remove(target)
        self.save_object(source.env, True)
        source.refresh_all()
        return target.title + " removed from room"
        
class EditAlias(Action):
    def __init__(self):
        Action.__init__(self, ("addalias", "delalias"))
        self.msg_class = "aliases"
        self.prep = ":"
        self.imm_level = IMM_LEVELS["creator"]
        self.help_text = "Usage:  addalias [target] : [new alias], delalias [target] : [old_alias]  \
            Multiple words aliases allowed.  If used on a monster or object, the template for all \
            such monsters or objects is modified"
        
    def execute(self, verb, source, args, target, command, **ignored):
        try:
            check_room(source, source.env)
        except BuildError as exp:
            return exp.msg
        
        edit_alias = find_extra_prep(self.prep, command)
        template = getattr(target, "template", None)
        if template:
            save_target = template
        elif target in source.env.extras or target in source.env.exits:
            save_target = source.env
        else:
            return "Invalid database target"
        if edit_alias in target.aliases:
            if verb[0] == "delalias":
                target.aliases.remove(edit_alias)
            else:
                return "Alias already exists"
        else:
            if verb[0] == "addalias":
                target.aliases.append(edit_alias)
            else:
                return "Alias does not exist"
        target.config_targets()   
        self.save_object(save_target)
        source.refresh_all()
        return "Alias modified " + ("[template]" if template else "")
    
class AddMob(BuildAction):
    def __init__(self):
        Action.__init__(self, "addmob")
        
    def build(self, source, room, area, target, args):
        if not args:
            return "Mob id required"
        
        mob_template = area.get_mobile(args[0])
        if not mob_template:
            return "Monster does not exist in this area"
        mob_reset = MobileReset(mob_template.mobile_id)
        try:
            mob_reset.mob_count = int(args[1])
        except (TypeError, IndexError):
            pass
        try:
            mob_reset.mob_max = int(args[2])
        except  (TypeError, IndexError):
            pass
        room.mobile_resets.append(mob_reset)
        self.save_object(room, True)
        return "Mobile reset created"

         
class DelMob(BuildAction):
    def __init__(self):
        Action.__init__(self, "delmob")
        
    def build(self, source, room, area, target, args):
        if not args:
            return "Mob id required"
            
        mobile_id = args[0]
        if ":" not in mobile_id:
            mobile_id = ":".join([room.area_id, mobile_id])
            
        found = False
        for mobile_reset in room.mobile_resets[:]:
            if mobile_reset.mobile_id == mobile_id:
                room.mobile_resets.remove(mobile_reset)
                found = True
                
        if not found:
            return "No resets for " + mobile_id + " in this room"
        
        self.save_object(room, True)
        return mobile_id + " removed from " + room.title
        
       
class ResetRoom(Action):
    def __init__(self):
        Action.__init__(self, "reset")
    
    def execute(self, source, args, **ignored):
        area = Action.mud.get_area(source.env.area_id) #@UndefinedVariable
        source.env.reset(area)
        return "Room reset"

class CreateRoom(Action):
    def __init__(self):
        Action.__init__(self, "createroom")
        self.imm_level = IMM_LEVELS["creator"]
        
    def execute(self, source, verb, args, command, **ignored):
        if not args:
            return "Room id must be specified for create"
        if ":" in args[0]:
            area_id, room_id = tuple(args[0].split(":"))
        else:
            area_id = source.env.area_id
            room_id = args[0]
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg
        if len(args) > 1:
            title = find_extra(verb, 1, command)
        else:
            title = "Area " + area_id + " room " + room_id
        room = Room(area_id + ":" + room_id, title, title)
        self.save_object(room)
        area.rooms.append(room)
        self.save_object(area)
        source.change_env(room)
        return source.parse("look")
            

class DelRoom(Action):
    def __init__(self):
        self.imm_level = IMM_LEVELS["creator"]
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
            if len(args) > 1:
                raise BuildError("Other room not found")
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
            