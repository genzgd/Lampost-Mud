from collections import defaultdict
from lampost.context.resource import m_requires, register
from lampost.gameops.action import make_action, ActionError, convert_verbs
from lampost.util.lmutil import StateError

m_requires('log', 'user_manager', 'session_manager', 'message_service', 'friend_service', 'dispatcher', __name__)
_mud_actions = {}

register('mud_actions', _mud_actions)
imm_actions = set()


def mud_action(verbs, msg_class=None, **kwargs):
    def dec_wrapper(func):
        action = make_action(func, msg_class=msg_class, **kwargs)
        for verb in convert_verbs(verbs):
            if verb in _mud_actions:
                error("Adding mud action for {}".format(verb))
            else:
                _mud_actions[verb] = action
    return dec_wrapper


def imm_action(verbs, msg_class=None, imm_level='creator', **kwargs):
    def dec_wrapper(func):
        imm_actions.add(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class, **kwargs)
    return dec_wrapper


@mud_action(('quit', 'log out'))
def quit_action(source, **_):
    source.check_logout()
    session_manager.logout(source.session)


@mud_action(("look", "l", "exa", "examine", "look at"), "examine")
def look(target_method, **kwargs):
    return target_method(**kwargs)


@mud_action('help')
def help_action(source, args, **_):
    if not args:
        source.display_line('Available actions:')
        action_verbs = defaultdict(list)
        for verb, action in _mud_actions.items():
            action_verbs[action].append(" ".join(list(verb)))
        verb_lists = ["/".join(verbs) for verbs in action_verbs.values()]
        return source.display_line(", ".join(sorted(verb_lists)))
    action = _mud_actions.get(args, None)
    if not action:
        raise ActionError("No matching command found")
    return getattr(action, "help_text", "No help available.")


@mud_action('friends')
def friends(source, **_):
    friend_list = friend_service.friend_list(source.dbo_id)
    return "Your friends are:<br/>&nbsp&nbsp{}".format(friend_list) if friend_list else "Alas, you are friendless."


@mud_action('friend', 'player')
def friend(source, target, **_):
    if source == target or friend_service.is_friend(source.dbo_id, target.dbo_id):
        return "{} is already your friend.".format(target.name)
    try:
        friend_service.friend_request(source, target)
    except StateError as exp:
        return exp.message
    return "Friend request sent"


@mud_action('unfriend')
def unfriend(source, args, **_):
    if not args or len(args) > 1:
        raise ActionError("Who do you want to unfriend?")
    unfriend_id = user_manager.name_to_id(args[0])
    friend_name = user_manager.id_to_name(unfriend_id)
    if friend_service.is_friend(source.dbo_id, unfriend_id):
        friend_service.del_friend(source.dbo_id, unfriend_id)
        message_service.add_message('system', "You unfriended {}.".format(friend_name), source.dbo_id)
        message_service.add_message('system', "{} unfriended you!".format(source.name), unfriend_id)
    else:
        raise ActionError("{} is not your friend".format(args[0]))


@mud_action('message')
def message(source, args, command, **_):
    if not args:
        raise ActionError("Message who?")
    if len(args) == 1:
        raise ActionError("Message what?")
    target_id = user_manager.name_to_id(args[0])
    if not user_manager.player_exists(target_id):
        raise ActionError("{} not found.".format(args[0]))
    message_service.add_message('player', command.partition(args[0])[2][1:], target_id, source.dbo_id)
    return "Message Sent"


@mud_action('block')
def block(source, args, **_):
    if not args or len(args) > 1:
        raise ActionError("Who do you want to block?")
    block_id = user_manager.name_to_id(args[0])
    block_name = user_manager.id_to_name(block_id)
    if not user_manager.player_exists(block_id):
        raise ActionError("No player named {}".format(block_name))
    if message_service.is_blocked(source, block_id):
        return "You have already blocked {}.".format(block_name)
    message_service.block_messages(source.dbo_id, block_id)
    return "You have blocked messages from {}.".format(block_name)


@mud_action('unblock')
def unblock(source, args, **_):
    if not args or len(args) > 1:
        raise ActionError("Who do you want to unblock?")
    block_id = user_manager.name_to_id(args[0])
    if message_service.is_blocked(source.dbo_id, block_id):
        message_service.unblock_messages(source.dbo_id, block_id)
        return "You unblock messages from {}".format(block_id)
    return "You are not blocking messages from {}".format(block_id)


@mud_action('follow', msg_class='follow')
def follow(source, target, target_method, **_):
    if hasattr(source, 'following'):
        return "You are already following {}.".format(source.following.name)
    target_method(source)
    source.following = target


@mud_action('unfollow')
def unfollow(source, args,  **_):
    if not hasattr(source, 'following'):
        return "You aren't following anyone."
    if args and args[0].lower() != source.following.name.lower():
        return "You aren't following {}.".format(args[0])
    source.display_line("You are no longer following {}".format(source.following.name))
    source.following.display_line("{} is no longer following you.".format(source.name))
    source.following.followers.remove(source)
    del source.following

@mud_action('abandon')
def abandon(source, **_):
    if source.dead:
        source.resurrect()
    else:
        source.display_line("You're not dead yet!")
