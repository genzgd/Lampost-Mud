from lampost.context.resource import m_requires
from lampost.mud.action import mud_action

m_requires(__name__, 'dispatcher')


class Group():
    def __init__(self, leader):
        self.leader = leader
        self.members = [leader]
        self.invites = invites



@mud_action('group', target_class='logged_in')
def invite(source, target):
    if target.group:
        return "{} is already in a group.".format(target.name)



@mud_action('accept', target_class='no_args')
def accept_group(source):
    if not source.group:
        return "You haven't been invited to a group"



