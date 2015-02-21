from lampost.comm.channel import Channel
from lampost.context.config import m_configured
from lampost.context.resource import m_requires
from lampost.env.room import Room, safe_room
from lampost.gameops.action import ActionError
from lampost.mud.action import mud_action, imm_actions

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'perm', 'user_manager', 'instance_manager',
           'message_service', 'friend_service')

m_configured(__name__, 'default_start_room')

_init_priority = 5000


def _post_init():
    global shout_channel, imm_channel
    shout_channel = Channel('shout', general=True)
    imm_channel = Channel('imm')
    register('player_create', _player_create)
    register('player_baptise', _baptise, priority=-100)
    register('imm_baptise', _imm_baptise, priority=-100)
    register('missing_env', _start_env)


def _player_create(player, user):
    if len(user.player_ids) == 1 and not player.imm_level:
        player.imm_level = perm_level('builder')
        update_immortal_list(player)
        dispatch('imm_level_change', player, 0)
        message_service.add_message('system', "Welcome!  Your first player has been given immortal powers.  Check out the 'Editor' window on the top menu.", player.dbo_id)
    player.room_id = default_start_room


def _baptise(player):
    player.baptise()
    shout_channel.add_sub(player)
    if player.imm_level:
        dispatch("imm_baptise", player)
    player.change_env(_start_env(player))


def _imm_baptise(player):
    player.can_die = False
    player.immortal = True
    imm_channel.add_sub(player)
    for cmd in imm_actions:
        if player.imm_level >= perm_level(cmd.imm_level):
            player.enhance_soul(cmd)
        else:
            player.diminish_soul(cmd)


def _start_env(player):
    instance = instance_manager.get(player.instance_id)
    instance_room = load_object(player.instance_room_id, Room, silent=True)
    player_room = load_object(player.room_id, Room, silent=True)

    if instance and instance_room:
        # Player is returning to an instance still in memory
        return instance.get_room(player.instance_room_id)

    if instance_room and not player_room:
        # Player has no 'non-instanced' room, so presumably was created in a new instanced tutorial/racial area
        instance = instance_manager.next_instance()
        return instance.get_room(player.instance_room_id)

    # If we get here whatever instance data was associated with the player is no longer valid
    del player.instance_id
    del player.instance_room_id

    if player_room:
        return player_room

    default_start = load_object(default_start_room, Room)
    if default_start:
        return default_start

    # This really should never happen
    error("Unable to find valid room for player login", stack_info=True)
    del player.room_id
    save_object(player)
    return safe_room


@mud_action(('quit', 'log out'))
def quit_action(source, **_):
    source.check_logout()
    dispatch('player_logout', source.session)


@mud_action(("look", "l", "exa", "examine", "look at"), "examine")
def look(target_method, **kwargs):
    return target_method(**kwargs)


@mud_action('friends')
def friends(source, **_):
    friend_list = friend_service.friend_list(source.dbo_id)
    return "Your friends are:<br/>&nbsp&nbsp{}".format(friend_list) if friend_list else "Alas, you are friendless."


@mud_action('friend', 'is_player')
def friend(source, target, **_):
    if source == target or friend_service.is_friend(source.dbo_id, target.dbo_id):
        return "{} is already your friend.".format(target.name)
    try:
        friend_service.friend_request(source, target)
    except ClientError as exp:
        return str(exp)
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


@mud_action('follow', 'follow')
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
    source.unfollow()

@mud_action('abandon')
def abandon(source, **_):
    if source.dead:
        source.resurrect()
    else:
        source.display_line("You're not dead yet!")
