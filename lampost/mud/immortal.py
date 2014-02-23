import pdb
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
from lampost.gameops.display import TELL_TO_DISPLAY

m_requires('session_manager', 'datastore', 'dispatcher', 'perm', 'email_sender', 'user_manager', __name__)

@imm_action('edit')
def edit(source, **ignored):
    check_perm(source, load_object(Area, source.env.parent_id))
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
                dest = ":".join([source.env.parent_id, dest])
            new_env = load_object(Room, dest)
    if new_env:
        source.change_env(new_env)
    else:
        raise ActionError("Cannot find " + dest)


@imm_action('summon')
def summon(source, args, **ignored):
    session = session_manager.player_session(args[0].lower())
    if not session:
        return "Player is not logged in"
    player = session.player
    check_perm(source, player)
    player.change_env(source.env)
    source.broadcast(s="You summon {N} into your presence.", e="{n} summons {N}!", t="You have been summoned!", target=player)


@imm_action('debug', 'supreme')
def debug(**ignored):
    pdb.set_trace()


@imm_action('patch', '__dict__', imm_level='supreme', prep=":", obj_target_class="args")
def patch(target, verb, args, command, **ignored):
    try:
        split_ix = args.index(":")
        prop = args[split_ix + 1]
        new_value = find_extra(verb, split_ix + 2, command)
    except (ValueError, IndexError):
        return "Syntax -- 'patch [target] [:] [prop_name] [new_value]'"
    if not new_value:
        return "New value required"
    if new_value == "None":
        new_value = None
    try:
        patch_object(target, prop, new_value)
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


@imm_action('force', msg_class="living", prep="to", obj_target_class="args")
def force(source, target, obj, **ignored):
    force_cmd = ' '.join(obj)
    if not force_cmd:
        return "Force {} to do what?".format(target.name)
    check_perm(source, target)
    target.display_line("{} forces you to {}.".format(source.name, force_cmd))
    target.parse(force_cmd)


@imm_action('unmake', 'general', target_class="env_living env_items")
def unmake(source, target, **ignored):
    if hasattr(target, 'is_player'):
        raise ActionError("You can't unmake players")
    if target in source.env.inven:
        source.broadcast(s="{N} is no more.", target=target)
        source.env.remove_inven(target)
        target.detach()
    elif target in source.env.denizens:
        source.broadcast(s="{N} is unmade", target=target)
        target.leave_env()
        target.detach()


@imm_action('toggle mortal', 'immortal',  self_target=True)
def toggle_mortal(target, **ignored):
    target.can_die = not target.can_die
    target.display_line("You can {} die.".format('now' if target.can_die else 'no longer'))


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
    source.display_line('&nbsp;&nbsp;')
    for line in target.describe():
        source.display_line(line, TELL_TO_DISPLAY)

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


@imm_action('promote', 'player', prep='to', obj_target_class='args', imm_level='admin')
def promote(source, target, obj, **ignored):
    if source == target:
        return "Let someone else do that."
    check_perm(source, target)
    if not obj:
        return "Promote {0} to what?".format(target.name)
    imm_level = perm_to_level(obj_key[0])
    if imm_level is None:
        return "That is not a valid level"
    target.imm_level = imm_level
    dispatch('imm_baptise', target)
    update_immortal_list(target)
    source.broadcast(s="You promote {N} to " + obj_key[0], t="{n} promotes you to " + obj_key[0] + "!", e="{N} gets promoted!", target=target)


@imm_action('run update', imm_level='supreme')
def run_update(source, args, **ignored):
    try:
        return lampost.setup.update.__dict__[args[0]](source, *args[1:])
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


@imm_action('status', 'combat_status', self_target=True)
def combat_status(target, **ignored):
    return substitute(target.combat_status(), target=target)


@imm_action('save', 'save_value')
def save(target, **ignored):
    save_object(target)
    return '{} saved.'.format(target.name)
