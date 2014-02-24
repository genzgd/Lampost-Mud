from collections import defaultdict
from lampost.datastore.dbo import DBOField, DBOTField
from lampost.gameops.action import action_handler, add_actions, remove_action, add_action

from lampost.comm.broadcast import Broadcast
from lampost.context.resource import m_requires
from lampost.gameops.display import SYSTEM_DISPLAY
from lampost.gameops.parser import ParseError, parse_actions, has_action
from lampost.model.item import BaseItem
from lampost.mud.inventory import InvenContainer

m_requires('log', __name__)


class Entity(BaseItem):
    size = DBOTField('medium')
    inven = DBOField(InvenContainer(), 'container')

    status = 'ok'
    living = True
    instance = None

    entry_msg = Broadcast(e='{n} materializes.', ea="{n} arrives from the {N}.", silent=True)
    exit_msg = Broadcast(e='{n} dematerializes.', ea="{n} leaves to the {N}", silent=True)

    def __init__(self, dbo_id=None):
        super(Entity, self).__init__(dbo_id)
        self.soul = defaultdict(set)
        self.inven_actions = defaultdict(set)
        self.followers = set()
        self.registrations = set()

    def baptise(self):
        add_actions(self.inven_actions, self.inven)

    def enhance_soul(self, action):
        add_action(self.soul, action)

    def diminish_soul(self, action):
        remove_action(self.soul, action)

    def add_inven(self, article):
        self.inven.append(article)
        add_action(self.inven_actions, article)

    def remove_inven(self, article):
        self.inven.remove(article)
        remove_action(self.inven_actions, article)

    def entity_enter_env(self, entity):
        pass

    def entity_leave_env(self, entity, ex):
        pass

    def parse(self, command):
        if command[0] == '\'':
            command = 'say {}'.format(command[1:])
        try:
            action, act_args = parse_actions(self, command)
            act_args['command'] = command
            act_args['source'] = self
            self.start_action(action, act_args)
        except ParseError as error:
            self.handle_parse_error(error, command)

    def filter_actions(self, matches):
        return matches

    @action_handler
    def start_action(self, action, act_args):
        if hasattr(action, 'prepare_action'):
            action.prepare_action(**act_args)
        self.process_action(action, act_args)
        self.check_follow(action, act_args)

    @action_handler
    def process_action(self, action, act_args):
        response = action(**act_args)
        if isinstance(response, basestring):
            self.display_line(response)
        elif response:
            self.output(response)

    def check_follow(self, action, act_args):
        if getattr(action, 'can_follow', False):
            for follower in self.followers:
                if has_action(follower, action, act_args['verb']):
                    follow_args = act_args.copy()
                    follow_args['source'] = follower
                    follower.start_action(action, follow_args)

    def handle_parse_error(self, error, command):
        self.display_line(error.message, SYSTEM_DISPLAY)

    def social(self, **_):
        pass

    def follow(self, source, **_):
        self.followers.add(source)
        source.broadcast(s="You start following {N}.", t="{n} starts following you.", e="{n} starts following {N}.", target=self)

    def examine(self, source, **_):
        super(Entity, self).examine(source, **_)
        source.display_line("{0} is carrying:".format(self.name))
        if self.inven:
            for article in self.inven:
                article.glance(source)
        else:
            source.display_line("Nothing")

    def change_env(self, new_env, ex=None):
        self.leave_env(ex)
        self.enter_env(new_env, ex)

    def leave_env(self, ex=None):
        if self.env:
            old_env = self.env
            self.env = None
            self.exit_msg.target = getattr(ex, 'dir_desc', None)
            old_env.entity_leaves(self, ex)

    def enter_env(self, new_env, ex=None):
        self.entry_msg.target = getattr(ex, 'from_desc', None)
        new_env.entity_enters(self, ex)
        new_instance = getattr(self.env, 'instance', None)
        if self.instance != new_instance:
            if self.instance:
                self.instance.remove_entity(self)
            if new_instance:
                new_instance.add_entity(self)
        if not self.instance and self.env.room_id:
            self.room_id = self.env.room_id
        self.env.examine(self)

    def broadcast(self, **kwargs):
        broadcast = Broadcast(**kwargs)
        broadcast.source = self
        if self.env:
            self.env.receive_broadcast(broadcast)

    def display_line(self, line, display='default'):
        pass

    def output(self, response):
        pass

    def can_see(self, target):
        return True

    def check_inven(self, article, quantity):
        pass

    def check_drop(self, article, quantity):
        pass

    def die(self):
        self.exit_msg = Broadcast(s="{n} expires, permanently.")
        for article in reversed(self.inven):
            article.current_slot = None
            article.drop(self)

        self.leave_env()
        self.status = 'dead'
        self.detach()

    def detach(self):
        super(Entity, self).detach()
        if self.instance:
            self.instance.remove_entity(self)
        for follower in self.followers:
            del follower.following
            follower.display_line("You are no longer following {}.".format(self.name))
        if hasattr(self, 'following'):
            self.following.display_line("{} is no longer following you.".format(self.name))
            del self.following
        self.equip_slots.clear()

    def equip_article(self, article):
        pass

    @property
    def display_status(self):
        return {'status': self.status}

    @property
    def dead(self):
        return self.status == 'dead'
