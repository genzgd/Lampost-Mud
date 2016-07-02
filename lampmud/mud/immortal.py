import pdb
import time

from lampost.di.resource import Injected, module_inject, get_resource
from lampost.gameops.action import ActionError
from lampost.server.user import User

import lampmud.setup.update

from lampmud.comm.broadcast import substitute

from lampmud.mud.action import imm_action
from lampost.util.lputil import find_extra, patch_object, str_to_primitive

sm = Injected('session_manager')
db = Injected('datastore')
ev = Injected('dispatcher')
perm = Injected('perm')
email = Injected('email_sender')
um = Injected('user_manager')
module_inject(__name__)


@imm_action('edit')
def edit(source, **_):
    perm.check_perm(source, db.load_object(source.env.parent_id, 'area'))
    return {'start_room_edit': source.env.dbo_id}


@imm_action('commands')
def commands(source, **_):
    verb_lists = ["/".join(list(verb)) for verb in source.soul_actions.all_actions().values()]
    return ", ".join(sorted(verb_lists))


@imm_action('timeit')
def timeit(source, command, **_):
    timed_command = command[command.find(' ') + 1:].strip()
    if timed_command.startswith('timeit'):
        return "Can't time timeit"
    start = time.time()
    source.parse(timed_command)
    ms = (time.time() - start) * 1000
    source.display_line("Time: {} ms".format(round(ms, 1)))


@imm_action('set flag', target_class='args', prep='on', obj_msg_class="flags", self_object=True)
def add_flag(source, target, obj, **_):
    try:
        flag_id = target[0]
    except IndexError:
        raise ActionError("Flag id required.")
    try:
        flag_value = target[1]
    except IndexError:
        flag_value = 'None'
    try:
        flag_value = str_to_primitive(flag_value)
    except ValueError:
        raise ActionError("Cannot parse {}".format(flag_value))
    obj.flags[flag_id] = flag_value
    source.display_line("Flag {} set to {} on {}.".format(flag_id, flag_value, obj.name))


@imm_action('clear flag', target_class='args', prep='from', obj_msg_class="flags", self_object=True)
def add_flag(source, target, obj, **_):
    try:
        flag_id = target[0]
    except IndexError:
        raise ActionError("Flag id required.")
    try:
        old_value = obj.flags.pop(flag_id)
    except KeyError:
        raise ActionError("Flag {} not set.".format(flag_id))
    source.display_line("Flag {} ({}) cleared {}.".format(flag_id, old_value, obj.name))


@imm_action('goto')
def goto(source, args, **_):
    if not args:
        raise ActionError("Go to whom? or to where?")
    dest = args[0].lower()
    session = sm.player_session(dest)
    if session:
        new_env = session.player.env
    else:
        area = db.load_object(dest, 'area', True)
        if area:
            dest_rooms = area.dbo_child_keys('room')
            if dest_rooms:
                new_env = db.load_object(dest_rooms[0], 'room', True)
            else:
                raise ActionError("No rooms in area {}.".format(args[0]))
        else:
            if ":" not in dest:
                dest = ":".join([source.env.parent_id, dest])
            new_env = db.load_object(dest, 'room', True)
    if new_env:
        source.change_env(new_env)
    else:
        raise ActionError("Cannot find " + dest)


@imm_action('summon')
def summon(source, args, **_):
    if not args:
        return "Summon whom?"
    session = sm.player_session(args[0].lower())
    if not session:
        return "Player is not logged in"
    player = session.player
    perm.check_perm(source, player)
    player.change_env(source.env)
    source.broadcast(s="You summon {N} into your presence.", e="{n} summons {N}!", t="You have been summoned!", target=player)


@imm_action('trace', imm_level='supreme')
def start_trace(**_):
    pdb.set_trace()


@imm_action('patch', '__dict__', imm_level='supreme', prep=":", obj_class="obj_args")
def patch(target, verb, args, command, **_):
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
    patch_object(target, prop, new_value)
    return "Object successfully patched"


@imm_action('patch_db', imm_level='supreme')
def patch_db(verb, args, command, **_):
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
    key = ':'.join([obj_type, obj_id])
    obj = db.load_object(key)
    if not obj:
        return "Object not found"
    patch_object(obj, prop, new_value)
    db.save_object(obj)
    return "Object " + key + " patched"


@imm_action('set home')
def set_home(source, **_):
    source.home_room = source.env.dbo_id
    source.display_line("{0} is now your home room".format(source.env.title))


@imm_action('force', msg_class="living", prep="_implicit_", obj_class="obj_args")
def force(source, target, obj, **_):
    force_cmd = ' '.join(obj)
    if not force_cmd:
        return "Force {} to do what?".format(target.name)
    perm.check_perm(source, target)
    target.display_line("{} forces you to {}.".format(source.name, force_cmd))
    target.parse(force_cmd)


@imm_action('unmake', 'general', target_class="env_living env_items inven")
def unmake(source, target, **_):
    if hasattr(target, 'is_player'):
        raise ActionError("You can't unmake players")
    if target in source.env.inven:
        source.broadcast(s="{N} is no more.", target=target)
        source.env.remove_inven(target)
    elif target in source.env.denizens:
        source.broadcast(s="{N} is unmade", target=target)
        target.leave_env()
    elif target in source.inven:
        source.check_drop(target)
        source.inven.remove(target)
        source.display_line("You unmake {}".format(target.name))
    try:
        target.detach()
    except AttributeError:
        pass


@imm_action('toggle mortal', 'immortal', target_class="living")
def toggle_mortal(target, **_):
    target.can_die = not target.can_die
    target.display_line("You can {} die.".format('now' if target.can_die else 'no longer'))


@imm_action('home')
def home(source, **_):
    if not getattr(source, 'home_room', None):
        return "Please set your home room first!"
    return goto(source=source, args=(source.home_room,))


@imm_action('register display')
def register_display(source, args, **_):
    if not args:
        return "No event specified"
    ev.register(args[0], source.display_line)
    source.display_line("Events of type {0} will now be displayed".format(args[0]))


@imm_action('unregister display')
def unregister_display(source, args, **_):
    ev.unregister_type(source, args[0])
    source.display_line("Events of type {0} will no longer be displayed".format(args[0]))


@imm_action('describe', 'describe')
def describe(source, target, **_):
    source.display_line('&nbsp;&nbsp;')
    for line in target.describe():
        source.display_line(line, 'tell_to')


@imm_action('reset')
def reset(source, **_):
    source.env.reset()
    return "Room reset"


@imm_action('reload')
def reload_room(source, **_):
    if source.env.instance:
        raise ActionError("Don't reload instanced rooms")
    source.env.reload()


@imm_action("log level", imm_level='supreme')
def log_level(args, **_):
    log = get_resource("log")
    if args:
        log.set_level(args[0])
    return "Log level at {}".format(log.level_desc)


@imm_action(('promote', 'demote'), 'is_player', prep='to', obj_class='obj_args', imm_level='admin')
def promote(source, verb, target, obj, **_):
    if source == target:
        return "Let someone else do that."
    perm.check_perm(source, target)
    if not obj:
        return "Promote {0} to what?".format(target.name)
    level_name = obj[0]
    imm_level = perm.perm_to_level(level_name)
    if imm_level is None:
        return "That is not a valid level."
    if imm_level == target.imm_level:
        return "{} is already a(n) {}".format(target.name, level_name)
    old_level = target.imm_level
    target.imm_level = imm_level
    perm.update_immortal_list(target)
    ev.dispatch('imm_update', target, old_level)
    ev.dispatch('imm_attach', target, old_level)
    target.session.append({'player_update': {'imm_level': imm_level}})
    source.broadcast(s="You {vb} {N} to {lvl}.", t="{n} {vb}s you to {lvl}!", e="{N} gets {vb}d!",
                     target=target, ext_fmt={'vb': verb, 'lvl': level_name})


@imm_action('run update', imm_level='supreme')
def run_update(source, args, **_):
    if not args:
        return "Update name required."
    try:
        return lampmud.setup.update.__dict__[args[0]](source, *args[1:])
    except KeyError:
        return "No such update."


@imm_action('email', imm_level='admin')
def email(verb, args, command, **_):
    if len(args) < 2:
        return "Player and message required"
    player = um.find_player(args[0])
    if not player:
        return "Player not found"
    user = db.load_object(player.user_id, User)
    message = find_extra(verb, 1, command)
    return email.send_targeted_email('Lampost Message', message, [user])


@imm_action('combat log')
def combat_log(source, **_):
    try:
        delattr(source.env, 'combat_log')
        return "Combat logging removed from {}".format(source.env.name)
    except AttributeError:
        source.env.combat_log = True
        return "Combat logging added to {}.".format(source.env.name)


@imm_action('status', 'combat_status', target_class="living")
def combat_status(target, **_):
    return substitute(target.combat_status(), target=target)


@imm_action('save', 'save_value')
def save(target, **_):
    db.save_object(target)
    return '{} saved.'.format(target.name)


@imm_action('scripts', 'scripts', 'admin')
def show_scripts(source, target, **_):
    if not target.scripts:
        return "No scripts"
    source.display_line("Scripts: ")
    for script in target.scripts:
        source.display_line("    {}".format(script.title))
