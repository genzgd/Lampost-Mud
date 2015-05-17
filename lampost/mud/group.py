from lampost.comm.channel import Channel
from lampost.context.resource import m_requires
from lampost.gameops.action import obj_action, ActionProvider
from lampost.model.item import BaseItem, gen_keys, Connected
from lampost.mud.action import mud_action

m_requires(__name__, 'dispatcher')


class Group(ActionProvider, Connected):
    target_keys = set(gen_keys('group'))

    def __init__(self, leader):
        leader.group = self
        self.leader = leader
        self.members = []
        self.invites = set()
        self.instance = None
        self.channel = Channel('gchat', 'next', aliases=('g', 'gc', 'gt', 'gtell', 'gsay', 'gs'))
        register('player_connect', self._player_connect)

    def join(self, member):
        if not self.members:
            self._add_member(self.leader)
        self.msg("{} has joined the group".format(member.name))
        self._add_member(member)
        self.invites.remove(member)

    def _add_member(self, member):
        member.group = self
        self.channel.add_sub(member)
        self.members.append(member)
        member.enhance_soul(self)

    def decline(self, member):
        self.leader.display_line("{} has declined your group invitation.".format(member.name))
        self.invites.remove(member)
        self._check_empty()

    @obj_action()
    def leave(self, source, **_):
        self._remove_member(source)
        if len(self.members) > 1 and source == self.leader:
            self.leader = self.members[0]
            self.msg("{} is now the leader of the group.".format(self.leader.name))
        else:
            self._check_empty()

    def _remove_member(self, member):
        self.msg("{} has left the group.".format(member.name))
        member.group = None
        member.diminish_soul(self)
        self.channel.remove_sub(member)
        self.members.remove(member)

    def msg(self, msg):
        self.channel.send_msg(msg)

    def _check_empty(self):
        if self.invites:
            return
        if len(self.members) == 1:
            self._remove_member(self.members[0])
        self.channel.disband()
        self.detach()

    def _player_connect(self, player, *_):
        if player in self.members:
            self.msg("{} has reconnected.".format(player.name))

    def detach_shared(self, member):
        self.leave(member)


class Invitation(BaseItem):
    title = "A group invitation"
    target_keys = set(gen_keys(title))

    def __init__(self, group, invitee):
        self.group = group
        self.invitee = invitee
        register_once(self.decline, seconds=60)

    def short_desc(self, *_):
        return self.title

    def long_desc(self, *_):
        return "An invitation to {}'s group.".format(self.group.leader.name)

    @obj_action(self_target=True)
    def accept(self, source, **_):
        source.display_line("You have joined {}'s group.".format(self.group.leader.name))
        self.group.join(self.invitee)
        source.remove_inven(self)
        detach_events(self)

    @obj_action(self_target=True)
    def decline(self, **_):
        self.invitee.display_line("You decline {}'s invitation.".format(self.group.leader.name))
        self.group.decline(self.invitee)
        self.detach()

    def detach(self):
        self.invitee.remove_inven(self)
        super().detach()


@mud_action(('group', 'invite'), target_class='logged_in')
def invite(source, target, **_):
    if target == source:
        return "Not really necessary.  You're pretty much stuck with yourself anyway."
    if target.group:
        if target.group == source.group:
            return "{} is already in your group!"
        target.display_line("{} attempted to invite you to a different group.".format(source.name))
        return "{} is already in a group.".format(target.name)
    if source.group:
        if target in source.group.invites:
            return "You have already invited {} to a group.".format(target.name)
    else:
        Group(source)
    source.group.invites.add(target)
    target.display_line(
        "{} has invited you to join a group.  Please 'accept' or 'decline' the invitation.".format(source.name))
    source.display_line("You invite {} to join a group.".format(target.name))
    target.add_inven(Invitation(source.group, target))
