from lampost.comm.channel import Channel
from lampost.context.resource import m_requires
from lampost.gameops.action import obj_action, ActionProvider
from lampost.model.item import BaseItem, gen_keys
from lampost.mud.action import mud_action

m_requires(__name__, 'dispatcher')


class Group():
    def __init__(self, leader):
        self.leader = leader
        self.members = [leader]
        self.invites = set()
        self.channel = Channel('gchat', current_pulse())
        self.join(leader)
        dispatcher.register('player_connect', self._player_connect)

    def join(self, member):
        member.group = self
        member.register_channel(self.channel)
        self.msg("{} has joined the group".format(member.name))
        self.members.append(member)
        GroupTag(self, member)

    def decline(self, member):
        self.msg("{} has declined your group invitation.".format(member.name))
        member.display_line("You decline {}'s invitation.".format(self.leader.name))
        self.invites.remove(member)

    def leave(self, member):
        member.group = None
        self.msg("{} has left the group.".format(member.name))
        self.members.remove(member)
        if self.members:
            if member == self.leader:
                self.leader = self.members[0]
                self.msg("{} is now the leader of the group.".format(self.leader_name))
        else:
            detach_events(self)

    def _player_connect(self, player, *_):
        if player in self.members:
            self.msg("{} has reconnected.".format(player.name))

    def msg(self, msg):
        self.channel.send_msg(msg)


class GroupTag(ActionProvider):
    def __init__(self, group, member):
        self.group = group
        self.member = member
        self.member.enhance_soul(self)

    @obj_action(verbs='leave', self_target=True)
    def detach(self, **_):
        self.group.leave(self.member)
        self.member.diminish_soul(self)
        detach_events(self)

    @obj_action(self_target=True)
    def group(self, **_):
        pass


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
        source.display_line("You have joined {}'s group.".format(self.group.leader))
        self.group.join(self.invitee)
        source.remove_inven(self)
        detach_events(self)

    @obj_action(self_target=True)
    def decline(self, **_):
        self.group.decline(self.invitee)
        self.invitee.remove_inven(self)
        detach_events(self)


@mud_action('group', target_class='logged_in')
def invite(source, target, **_):
    if target == source:
        return "Not really necessary.  You're pretty much stuck with yourself anyway."
    if target.group:
        return "{} is already in a group.".format(target.name)
    if source.group:
        if target in source.group.invites:
            return "You have already invited {} to a group.".format(target.name)
    else:
        Group(source)
    source.group.invites.add(target)
    target.display_line("{} has invited you to join a group.  Please 'accept' or 'decline' the invitation.".format(source.name))
    source.display_line("You invite {} to join a group.".format(target.name))
    target.add_inven(Invitation(source.group, target))