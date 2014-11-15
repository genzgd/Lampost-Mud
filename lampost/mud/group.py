from lampost.context.resource import m_requires
from lampost.gameops.action import obj_action, ActionProvider
from lampost.gameops.display import GROUP_DISPLAY
from lampost.gameops.parser import parse_chat
from lampost.mud.action import mud_action

m_requires(__name__, 'dispatcher')


class Group(ActionProvider):
    def __init__(self, leader):
        self.leader = leader
        self.members = {leader}
        self.invites = set()
        dispatcher.register('player_connect', self._player_connect)

    def _player_connect(self, player, *_):
        if player in self.members:
            self.group_message("{} has reconnected.".format(player), player)

    def group_message(self, msg, exclude):
        for member in self.members:
            if member != exclude:
                member.display_line(msg, GROUP_DISPLAY)

    @obj_action()
    def gchat(self, source, verb, command):
        self.group_message(parse_chat(verb, command), source)


class Invitation():
    def __init__(self, group, invitee):
        self.group = group
        self.invitee = invitee

    def accept(self):
        join_msg = "{} has joined the group".format(source.name)
        for member in self.group.members:
            member.display_line(join_msg)
        self.group.members.add(self.invitee)
        self.invitee.display_line("You have joined {}'s group.".format(self.group.leader))
        self.group.invites.remove(self)
        self.invitee.enhance_soul(self.group)
        del self.invitee.group_invite

    def decline(self):
        self.group.leader.display_line("{} has declined your group invitation".format(self.invitee.name))
        self.group.invites.remove(self)
        del self.invitee.group_invite


@mud_action('group', target_class='logged_in')
def invite(source, target, **_):
    if target == source:
        return "Not really necessary.  You're pretty much stuck with yourself anyway."
    if hasattr(target, 'group'):
        return "{} is already in a group.".format(target.name)
    if not hasattr(source, 'group'):
        group = Group(source)
        source.group = group
        source.enhance_soul(group)
    invitation = Invitation(group, target)
    source.group.invites.add(invitation)
    target.display_line("{} has invited you to join a group.  Please 'accept' or 'decline' the invitation.".format(source.name))
    source.display_line("You invite {} to join a group.".format(target.name))
    target.group_invite = invitation


@mud_action('accept')
def accept_group(source, **_):
    if not source.group_invite:
        return "You haven't been invited to a group."
    source.group_invite.accept()


@mud_action('decline')
def decline_group(source, **_):
    if not hasattr(source, 'group_invite'):
        return "You haven't been invited to a group."
    source.group_invite.decline()
