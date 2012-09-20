from immortal import IMM_LEVELS
from lampost.player.player import Player
from lampost.env.room import Room
from lampost.util.lmutil import ljust, find_extra_prep
from lampost.dto.display import Display, DisplayLine
from lampost.action.action import Action
from lampost.mobile.mobile import MobileReset
from lampost.model.article import ArticleTemplate, ArticleReset

BUILD_ROOM = Room("buildroom")

class BuildMode(Action):
    imm_level = IMM_LEVELS["creator"]

    def __init__(self):
        Action.__init__(self, "buildmode")

    def execute(self, source, **ignored):
        current = getattr(source, "build_mode", False)
        source.build_mode = not current
        return "Build Mode is {0}".format("On" if source.build_mode else "Off")


class ItemList(Action):
    imm_level = IMM_LEVELS["creator"]

    def __init__(self):
        Action.__init__(self, "itemlist")

    def execute(self, source, args, **ignored):
        if args:
            area_id = args[0]
        else:
            area_id = source.env.area_id
        area = self.mud.get_area(area_id)
        if not area:
            return "Invalid area"
        if not area.articles:
            return "No articles defined"
        display = Display()
        for article in area.articles:
            display.append(DisplayLine(ljust(article.dbo_id.split(":")[1], 20) + ljust(article.title, 20) + unicode(article.level)))
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


class EditAreaMob(Action):
    imm_level = IMM_LEVELS["creator"]

    def __init__(self):
        Action.__init__(self, ("delareamob", "mlevel", "mname", "mdesc"))

    def execute(self, source, verb, args, command, **ignored):
        area_id = source.env.area_id
        if not args:
            return "mob id required"
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg

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

class CreateItem(Action):
    imm_level = IMM_LEVELS["creator"]

    def __init__(self):
        Action.__init__(self, "areaitem")

    def execute(self, source, args, command, **ignored):
        area_id = source.env.area_id
        if not args:
            return "item id required"
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg

        article_id = ":".join([area_id, args[0]])
        if area.get_article(article_id):
            return article_id + " already exists in this area"

        title = command.partition(args[0])[2][1:]
        if not title:
            title = area.name + " " + args[0]
        template = ArticleTemplate(article_id, title)
        self.save_object(template)
        area.articles.append(template)
        self.save_object(area)


class EditAreaItem(Action):
    imm_level = IMM_LEVELS["creator"]

    def __init__(self):
        Action.__init__(self, ("delareaitem", "ilevel", "iname", "idesc", "iweight"))

    def execute(self, source, verb, args, command, **ignored):
        area_id = source.env.area_id
        if not args:
            return "item id required"
        try:
            area = check_area(source, area_id)
        except BuildError as exp:
            return exp.msg

        article_template = area.get_article(args[0])
        if not article_template:
            return "Monster does not exist in this area"

        if verb[0] == "delareaitem":
            article_resets = list(area.find_mobile_resets(article_template.article_id))
            if article_resets:
                if len(args) < 2 or args[1] != "force":
                    return "Item is used in rooms.  Use 'force' option to remove from rooms"
                for room, article_reset in article_resets:
                    room.mobile_resets.remove(article_reset)
                    self.save_object(room, True)

            area.article.remove(article_template)
            self.save_object(area)
            return article_template.article_id + " deleted."

        if len(args) < 2:
            return "Value required"

        if verb[0] == "ilevel":
            try:
                article_template.level = int(args[1])
            except TypeError:
                return "Invalid level"

        if verb[0] == "iweight":
            try:
                article_template.weight = int(args[1])
            except TypeError:
                return "Invalid weight"
        else:
            value = " ".join(command.split(" ")[2:])
            if verb[0] == "idesc":
                article_template.desc = value
            elif verb[0] == "iname":
                article_template.title = value
        self.save_object(article_template)
        return article_template.article_id + " updated"



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
                if not target.aliases:
                    target.aliases = []
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


class AddItem(BuildAction):
    def __init__(self):
        Action.__init__(self, "additem")

    def build(self, source, room, area, target, args):
        if not args:
            return "Item id required"

        article_template = area.get_article(args[0])
        if not article_template:
            return "Item does not exist in this area"
        article_reset = ArticleReset(article_template.article_id)
        try:
            article_reset.article_count = int(args[1])
        except (TypeError, IndexError):
            pass
        try:
            article_reset.article_max = int(args[2])
        except (TypeError, IndexError):
            pass
        room.article_resets.append(article_reset)
        self.save_object(room, True)
        return "Item reset created"


class DelItem(BuildAction):
    def __init__(self):
        Action.__init__(self, "delitem")

    def build(self, source, room, area, target, args):
        if not args:
            return "Item id required"

        article_id = args[0]
        if ":" not in article_id:
            article_id = ":".join([room.area_id, article_id])

        found = False
        for article_reset in room.article_resets[:]:
            if article_reset.article_id == article_id:
                room.article_resets.remove(article_reset)
                found = True

        if not found:
            return "No resets for " + article_id + " in this room"

        self.save_object(room, True)
        return article_id + " removed from " + room.title

class ResetRoom(Action):
    def __init__(self):
        Action.__init__(self, "reset")

    def execute(self, source, args, **ignored):
        area = Action.mud.get_area(source.env.area_id) #@UndefinedVariable
        source.env.reset(area)
        return "Room reset"






