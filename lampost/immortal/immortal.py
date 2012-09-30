from lampost.comm.broadcast import SingleBroadcast
from lampost.context.resource import m_requires
from lampost.dto.display import Display, DisplayLine
from lampost.dto.rootdto import RootDTO
from lampost.mud.action import imm_action
from lampost.player.player import Player
from lampost.util.lmutil import find_extra, patch_object, PatchError

m_requires('sm', 'mud', 'datastore', 'perm', __name__)

@imm_action('edit')
def edit(source, **ignored):
    check_perm(source, mud.get_area(source.env.area_id))
    return RootDTO(start_room_edit=source.env.dbo_id)


@imm_action(('cmds', 'commands'))
def cmds(source, **ignored):
    soul_actions = [action for action in source.soul if getattr(action, 'imm_level', None)]
    verb_lists = ["/".join([" ".join(list(verb)) for verb in action.verbs]) for action in soul_actions]
    return ", ".join(sorted(verb_lists))


@imm_action('goto')
def goto(source, args, **ignored):
    if not args:
        return "Go to whom? or to where?"
    dest = args[0].lower()
    if dest == 'area' and len(args) > 1:
        area = mud.get_area(args[1])
        if not area:
            return "Area does not exist"
        if not area.rooms:
            return "Area has no rooms!"
        new_env = area.first_room
    else:
        session = sm.user_session(dest)
        if session:
            new_env = session.player.env
        else:
            if not ":" in dest:
                dest = ":".join([source.env.area_id, dest])
            new_env = mud.find_room(dest)
    if new_env:
        source.change_env(new_env)
        return source.parse("look")
    return "Cannot find " + dest


@imm_action('summon')
def summon(source, args, **ignored):
    session = sm.user_session(args[0].lower())
    if not session:
        return "Player is not logged in"
    player = session.player
    check_perm(source, player)
    player.change_env(source.env)
    session.append(player.parse('look'))
    session.append(Display("You have been summoned"))
    return "You summon " + player.name + " into your presence."


@imm_action('patch', imm_level='supreme')
def patch(source, verb, args, command, **ignored):
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
    try:
        patch_object(target_list[0][0], prop, new_value)
    except PatchError as exp:
        return exp.message
    return "Object successfully patched"


@imm_action('patchdb', imm_level='supreme')
def patch_db(verb, args, command, **ignored):
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
    key = ":".join([obj_type, obj_id])
    if obj_type == "player":
        obj = load_object(Player, obj_id)
    else:
        obj = load_cached(key)
    if not obj:
        return "Object not found"
    try:
        patch_object(obj, prop, new_value)
    except PatchError as exp:
        return exp.message

    save_object(obj)
    return "Object " + key + " patched"


@imm_action('sethome')
def sethome(source, **ignored):
    source.home_room = source.env.dbo_id


@imm_action('zap', msg_class='damage')
def zap(source, target_method, **ignored):
    target_method(1000000)
    return SingleBroadcast(source, "An immortal recklessly wields power.")

@imm_action('unmake', 'general')
def unmake(source, target, **ignored):
    if target.env == source.env:
        target.leave_env()
        title = target.title
        del target
        return title + " is no more."
    return "Can only unmake things in the room."

@imm_action('home')
def home(source, **ignored):
    return goto(source=source, args=(source.home_room,))


@imm_action('register display')
def register_display(source, args, **ignored):
    if not args:
        return "No event specified"
    source.register(args[0], source.display_line)


@imm_action('unregister display')
def unregister_display(source, args, **ignored):
    source.unregister_type(args[0], source.display_line)


@imm_action('describe')
def describe(source, args, **ignored):
    if not args:
        target = source.env
    else:
        target = load_cached(args[0])
    if not target:
        return "No object with that key found"
    display = Display(" ")
    for line in target.describe():
        display.append(DisplayLine(line))
    return display


@imm_action('buildmode')
def build_mode(source, **ignored):
    current = getattr(source, "build_mode", False)
    source.build_mode = not current
    return "Build Mode is {0}".format("On" if source.build_mode else "Off")


@imm_action('reset')
def reset(source, **ignored):
    area = mud.get_area(source.env.area_id)
    source.env.reset(area)
    return "Room reset"


@imm_action('citadel')
def citadel(source, **ignored):
    return goto(source=source, args=('immortal_citadel:0',))
