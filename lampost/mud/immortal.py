import lampost.setup.update

from lampost.client.user import User
from lampost.comm.broadcast import substitute
from lampost.env.room import Room
from lampost.model.area import Area
from lampost.gameops.action import ActionError
from lampost.context.resource import m_requires, get_resource
from lampost.mud.action import imm_action
from lampost.model.player import Player
from lampost.util.lmutil import find_extra, patch_object, PatchError

m_requires('session_manager', 'datastore', 'dispatcher', 'perm', 'email_sender', 'user_manager', __name__)

@imm_action('edit')
def edit(source, **ignored):
    check_perm(source, load_object(Area, source.env.area_id))
    return {'start_room_edit': source.env.dbo_id}


@imm_action(('cmds', 'commands'))
def cmds(source, **ignored):
    verb_lists = [" ".join(["/".join(list(verb)) for verb in source.soul])]
    return ", ".join(sorted(verb_lists))


@imm_action('goto')
def goto(source, args, **ignored):
    if not args:
        raise ActionError("Go to whom? or to where?")
    dest = args[0].lower()
    if dest == 'area' and len(args) > 1:
        area = load_object(Area, args[1])
        if not area:
            raise ActionError("Area does not exist")
        if not area.rooms:
            raise ActionError("Area has no rooms!")
        new_env = area.first_room
    else:
        session = session_manager.player_session(dest)
        if session:
            new_env = session.player.env
        else:
            if not ":" in dest:
                dest = ":".join([source.env.area_id, dest])
            new_env = load_object(Room, dest)
    if new_env:
        source.change_env(new_env)
        return source.parse("look")
    raise ActionError("Cannot find " + dest)


@imm_action('summon')
def summon(source, args, **ignored):
    session = session_manager.player_session(args[0].lower())
    if not session:
        return "Player is not logged in"
    player = session.player
    check_perm(source, player)
    player.change_env(source.env)
    player.parse('look')
    source.broadcast(s="You summon {N} into your presence.", e="{n} summons {N}!", t="You have been summoned!", target=player)


@imm_action('patch', imm_level='supreme')
def patch(source, verb, args, command, **ignored):
    try:
        split_ix = args.index(":")
        target_id = args[:split_ix]
        prop = args[split_ix + 1]
        new_value = find_extra(verb, split_ix + 2, command)
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


@imm_action('patch_db', imm_level='supreme')
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
    if obj_type == "player":
        obj = load_object(Player, obj_id)
    else:
        obj = load_cached(obj_type, obj_id)
    if not obj:
        return "Object not found"
    try:
        patch_object(obj, prop, new_value)
    except PatchError as exp:
        return exp.message

    save_object(obj)
    return "Object " + key + " patched"


@imm_action('set home')
def set_home(source, **ignored):
    source.home_room = source.env.dbo_id
    source.display_line("{0} is now your home room".format(source.env.title))


@imm_action('force')
def force(source, command, **ignored):
    space_ix = command.find(" ")
    if space_ix == -1:
        raise ActionError("Force who?")
    remainder = command[space_ix + 1:]
    words = tuple(remainder.split(' '))
    match = None
    for ix in xrange(0, len(words)):
        space_ix = remainder.find(' ')
        if space_ix == -1:
            remainder = None
        else:
            remainder = remainder[space_ix + 1:]
        target = source.target_key_map.get(words[:ix + 1])
        if target and hasattr(target, 'parse'):
            if match:
                return "Ambiguous target"
            match = target, remainder
    if not match:
        return "No target found"
    target, force_cmd = match
    if not force_cmd:
        return "Force {} to do what?".format(target.name)
    check_perm(source, target)
    target.display_line("{} forces you to {}.".format(source.name, force_cmd))
    target.parse(force_cmd)


@imm_action('unmake', 'general')
def unmake(source, target, **ignored):
    if target.env == source.env:
        source.broadcast(s="{N} is no more.", target=target)
        target.leave_env()
        del target
    else:
        return "Can only unmake things in the room."


@imm_action('home')
def home(source, **ignored):
    if not getattr(source, 'home_room', None):
        return "Please set your home room first!"
    return goto(source=source, args=(source.home_room,))


@imm_action('register display')
def register_display(source, args, **ignored):
    if not args:
        return "No event specified"
    register(args[0], source.display_line)
    source.display_line("Events of type {0} will now be displayed".format(args[0]))


@imm_action('unregister display')
def unregister_display(source, args, **ignored):
    unregister_type(source, args[0])
    source.display_line("Events of type {0} will no longer be displayed".format(args[0]))


@imm_action('describe', 'describe')
def describe(source, target, **ignored):
    for line in target.rec_describe():
        source.display_line(line)


@imm_action('build mode')
def build_mode(source, **ignored):
    current = getattr(source, "build_mode", False)
    source.build_mode = not current
    return "Build Mode is {0}".format("On" if source.build_mode else "Off")


@imm_action('reset')
def reset(source, **ignored):
    source.env.reset()
    return "Room reset"


@imm_action("log level", imm_level='supreme')
def log_level(args, **ignored):
    log = get_resource("log")
    if args:
        log._set_level(args[0])
    return "Log level at {0}".format(log.level_desc)


@imm_action('promote', 'player', prep='to', obj_msg_class='args', imm_level='admin')
def promote(source, target, obj, **ignored):
    if source == target:
        return "Let someone else do that."
    check_perm(source, target)
    if not obj:
        return "Promote {0} to what?".format(target.name)
    imm_level = perm_to_level(obj[0])
    if imm_level is None:
        return "That is not a valid level"
    target.imm_level = imm_level
    dispatch('imm_baptise', target)
    update_immortal_list(target)
    source.broadcast(s="You promote {N} to " + obj[0], t="{n} promotes you to " + obj[0] + "!", e="{N} gets promoted!", target=target)


@imm_action('run update', imm_level='supreme')
def run_update(source, args, **ignored):
    try:
        return lampost.setup.update.__dict__[args[0]](source)
    except KeyError:
        return "No such update."


@imm_action('email', imm_level='admin')
def email(verb, args, command, **ignored):
    if len(args) < 2:
        return "Player and message required"
    player = user_manager.find_player(args[0])
    if not player:
        return "Player not found"
    user = load_object(User, player.user_id)
    message = find_extra(verb, 1, command)
    return email_sender.send_targeted_email('Lampost Message', message, [user])


@imm_action('combat log')
def combat_log(source, **ignored):
    try:
        delattr(source.env, 'combat_log')
        return "Combat logging removed from {}".format(source.env.name)
    except AttributeError:
        source.env.combat_log = True
        return "Combat logging added to {}.".format(source.env.name)


@imm_action('status', 'status', self_target=True)
def status(target, **ignored):
    return substitute(target.rec_status(), target=target)


@imm_action('save', 'has_save_value', self_target=True)
def save(target, **ignored):
    save_object(target)
    return '{} saved.'.format(target.name)
