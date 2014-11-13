from lampost.context.resource import m_requires
from lampost.mud.action import mud_action

m_requires(__name__, 'dispatcher')


class Group():
    def __init__(self, leader):
        self.leader = leader
        self.members = set(leader)
        self.invites = set()


@mud_action('group', target_class='logged_in')
def invite(source, target, **_):
    if target == source:
        return "Not really necessary.  You're pretty much stuck with yourself anyway."
    if target.group:
        if target in target.group.members:
            return "{} is already in a group.".format(target.name)
        return "{} is considering a different group invitation."
    if not source.group:
        source.group = Group(source)
    source.group.invites.add(target)
    target.display_line("{} has invited you to join a group.  Please 'accept' or 'decline' the invitation.")
    target.group = source.group


@mud_action('accept')
def accept_group(source, **_):
    if not source.group:
        return "You haven't been invited to a group."
    source.group.invites.remove(source)
    join_msg = "{} has joined the group".format(source.name)
    for member in source.group.members:
        member.display_line(join_msg)
    source.group.members.add(source)
    source.display_line("You have joined {}'s group".format(source.group.leader))


@mud_action('decline')
def decline_group(source, **_):
    source.group.invites.remove(source)
    source.group.leader.display_line("{} has declined your group invitation".format(source.name))
    del source.group




