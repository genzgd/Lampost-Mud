import html

from lampost.di.app import on_app_start
from lampost.server.channel import Channel
from lampost.di.config import config_value
from lampost.di.resource import Injected, module_inject
from lampost.gameops.action import ActionError
from lampost.server.link import link_route
from lampost.util.lputil import ClientError

from lampmud.mud.action import mud_action, imm_actions

log = Injected('log')
db = Injected('datastore')
ev = Injected('dispatcher')
perm = Injected('perm')
um = Injected('user_manager')
instance_manager = Injected('instance_manager')
message_service = Injected('message_service')
friend_service = Injected('friend_service')
module_inject(__name__)


@on_app_start(priority=2000)
def _start():
    global shout_channel, imm_channel
    shout_channel = Channel('shout', general=True)
    imm_channel = Channel('imm')
    ev.register('player_create', _player_create)
    ev.register('player_attach', _player_attach, priority=-100)
    ev.register('player_connect', _player_connect)
    ev.register('missing_env', _start_env)
    ev.register('imm_attach', _imm_attach, priority=-50)


@link_route('action')
def _action(player, action, **_):
    player.parse(html.escape(action.strip(), False))


def _player_create(player, user):
    if len(user.player_ids) == 1 and not player.imm_level:
        player.imm_level = perm.perm_level('builder')
        perm.update_immortal_list(player)
        ev.dispatch('imm_update', player, 0)
        message_service.add_message('system', "Welcome!  Your first player has been given immortal powers.  Check out the 'Editor' window on the top menu.", player.dbo_id)
    player.room_id = config_value('default_start_room')


def _player_attach(player):
    shout_channel.add_sub(player)
    ev.dispatch('imm_attach', player, 0)
    player.change_env(_start_env(player))


def _player_connect(player, *_):
    player.status_change()


def _imm_attach(player, old_level):
    player.can_die = player.imm_level == 0
    player.immortal = not player.can_die
    if player.immortal and not old_level:
        imm_channel.add_sub(player)
    elif not player.immortal and old_level:
        imm_channel.remove_sub(player)
    for cmd in imm_actions:
        if player.imm_level >= perm.perm_level(cmd.imm_level):
            player.enhance_soul(cmd)
        else:
            player.diminish_soul(cmd)


def _start_env(player):
    instance = instance_manager.get(player.instance_id)
    instance_room = db.load_object(player.instance_room_id, 'room', silent=True)
    player_room = db.load_object(player.room_id, 'room', silent=True)

    if instance and instance_room:
        # Player is returning to an instance still in memory
        return instance.get_room(instance_room)

    if instance_room and not player_room:
        # Player has no 'non-instanced' room, so presumably was created in a new instanced tutorial/racial area
        instance = instance_manager.next_instance()
        return instance.get_room(instance_room)

    # If we get here whatever instance data was associated with the player is no longer valid
    del player.instance_id
    del player.instance_room_id

    if player_room:
        return player_room

    return db.load_object(config_value('default_start_room'), 'room')


@mud_action(('quit', 'log out'))
def quit_action(source):
    source.check_logout()
    ev.dispatch('player_logout', source.session)


@mud_action(("l", "look", "examine", "look at"), "examine")
def look(source, target):
    return target.examine(source)


@mud_action('friends')
def friends(source):
    friend_list = friend_service.friend_list(source.dbo_id)
    return "Your friends are:<br/>&nbsp&nbsp{}".format(friend_list) if friend_list else "Alas, you are friendless."


@mud_action('blocks')
def blocks(source):
    blocked = message_service.block_list(source.dbo_id)
    return "You have blocked:<br/>&nbsp&nbsp{}".format(blocked) if blocked else "You have not blocked anyone."


@mud_action('friend', target_class='player_online')
def friend(source, target):
    if message_service.is_blocked(target.dbo_id, source.dbo_id):
        raise ActionError("You are blocked from sending messages to {}.".format(target.name), 'system')
    if friend_service.is_friend(source.dbo_id, target.dbo_id):
        return "{} is already your friend.".format(target.name)
    try:
        friend_service.friend_request(source, target)
    except ClientError as exp:
        return str(exp)
    return "Friend request sent"


@mud_action('unfriend', target_class='player_env player_db')
def unfriend(source, target):
    if friend_service.is_friend(source.dbo_id, target.dbo_id):
        friend_service.del_friend(source.dbo_id, target.dbo_id)
        message_service.add_message('system', "You unfriended {}.".format(target.name), source.dbo_id)
        message_service.add_message('system', "{} unfriended you!".format(source.name), target.dbo_id)
    else:
        raise ActionError("{} is not your friend".format(target.name))


@mud_action('message', target_class='player_env player_db self', obj_class='cmd_str')
def message(source, target, obj):
    message_service.add_message('player', obj, target.dbo_id, source.dbo_id)
    return "Message Sent"


@mud_action('block', target_class='player_env player_db')
def block(source, target):
    if message_service.is_blocked(source.dbo_id, target.dbo_id):
        return "You have already blocked {}.".format(target.name)
    message_service.block_messages(source.dbo_id, target.dbo_id)
    return "You have blocked messages from {}.".format(target.name)


@mud_action('unblock', target_class='player_env player_db')
def unblock(source, target):
    if message_service.is_blocked(source.dbo_id, target.dbo_id):
        message_service.unblock_messages(source.dbo_id, target.dbo_id)
        return "You unblock messages from {}".format(target.name)
    return "You are not blocking messages from {}".format(target.name)


@mud_action('follow', 'followers')
def follow(source, target):
    if hasattr(source, 'following'):
        return "You are already following {}.".format(source.following.name)
    source.follow(target)
    source.following = target


@mud_action('unfollow', target_class="cmd_str_opt")
def unfollow(source, target):
    if not hasattr(source, 'following'):
        return "You aren't following anyone."
    if target and target.lower() != source.following.name.lower():
        return "You aren't following {}.".format(target)
    source.unfollow()


@mud_action('abandon')
def abandon(source):
    if source.dead:
        source.resurrect()
    else:
        source.display_line("You're not dead yet!")


#@mud_action('mark', 'mark', prep='as', obj_class=)
#def mark(source, target, )
