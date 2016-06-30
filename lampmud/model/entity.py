import itertools

from lampost.db.dbo import DBOAspect
from lampost.db.dbofield import DBOField
from lampost.event.zone import Attachable
from lampost.gameops.action import action_handler, ActionCache
from lampost.gameops.parser import ParseError, parse_actions, has_action
from lampost.di.resource import Injected, module_inject

from lampmud.comm.broadcast import Broadcast, BroadcastMap

log = Injected('log')
mud_actions = Injected('mud_actions')
module_inject(__name__)


class Entity(DBOAspect, Attachable):
    inven = DBOField([], 'untyped')

    status = 'ok'
    living = True
    instance = None

    entry_msg = BroadcastMap(e='{n} materializes.', ea="{n} arrives from the {N}.")
    exit_msg = BroadcastMap(e='{n} dematerializes.', ea="{n} leaves to the {N}.")

    def _on_attach(self):
        self._soul_objects = set()
        self.inven_actions = ActionCache()
        self.inven_actions.add(self.inven)
        self.followers = set()
        self.soul_actions = ActionCache()

    def _on_detach(self):
        for follower in self.followers:
            del follower.following
            follower.display_line("You are no longer following {}.".format(self.name))
        for item in list(itertools.chain(self.inven, self._soul_objects)):
            if hasattr(item, 'detach'):
                item.detach()
            if hasattr(item, 'detach_shared'):
                item.detach_shared(self)
        self.unfollow()
        self.leave_env()
        del self.soul_actions
        del self.inven_actions
        del self._soul_objects

    def _on_reload(self):
        if self.attached:
            self.inven_actions.refresh(self.inven)
            self.soul_actions.refresh(self._soul_objects)

    @property
    def current_actions(self):
        return [self.env.current_actions, self.inven_actions, self.soul_actions, mud_actions]

    def enhance_soul(self, action):
        self._soul_objects.add(action)
        self.soul_actions.add(action)

    def diminish_soul(self, action):
        if action in self._soul_objects:
            self._soul_objects.remove(action)
            self.soul_actions.remove(action)

    def add_inven(self, article):
        self.inven.append(article)
        self.inven_actions.add(article)

    def remove_inven(self, article):
        try:
            self.inven.remove(article)
        except ValueError:
            pass
        self.inven_actions.remove(article)

    def entity_enter_env(self, *_):
        pass

    def entity_leave_env(self, *_):
        pass

    def parse(self, command):
        if command.startswith("'"):
            command = 'say ' + command[1:].strip()
        elif command.startswith(':'):
            command = 'emote ' + command[1:].strip()
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
        if isinstance(response, str):
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
        self.display_line(error.client_message, 'system')

    def social(self, **_):
        pass

    def follow(self, source, **_):
        self.followers.add(source)
        source.broadcast(s="You start following {N}.", t="{n} starts following you.", e="{n} starts following {N}.", target=self)

    def unfollow(self):
        following = getattr(self, 'following', None)
        if following:
            self.display_line("You are no longer following {}".format(following.name))
            following.display_line("{} is no longer following you.".format(self.name))
            following.followers.remove(self)
            del self.following

    def examine(self, source, **_):
        super().examine(source, **_)
        source.display_line("{0} is carrying:".format(self.name))
        if self.inven:
            for article in self.inven:
                article.glance(source)
        else:
            source.display_line("Nothing")

    def change_env(self, new_env, exit_action=None):
        if new_env:
            self.leave_env(exit_action)
            self.enter_env(new_env, exit_action)
        else:
            log.error("Entity {} changed to null environment", self.name)

    def leave_env(self, exit_action=None):
        if self.env:
            old_env = self.env
            self.env = None
            exit_msg = Broadcast(getattr(exit_action, 'exit_msg', self.exit_msg), self, exit_action, silent=True)
            old_env.entity_leaves(self, exit_action, exit_msg)

    def enter_env(self, new_env, enter_action=None):
        entry_msg = Broadcast(getattr(enter_action, 'entry_msg', self.entry_msg), self, silent=True)
        entry_msg.target = getattr(enter_action, 'from_name', None)
        new_env.entity_enters(self, enter_action, entry_msg)
        new_instance = getattr(self.env, 'instance', None)
        if self.instance != new_instance:
            if self.instance:
                self.instance.remove_entity(self)
                del self.instance_id
            if new_instance:
                new_instance.add_entity(self)
                self.instance_id = new_instance.instance_id
        if self.instance:
            self.instance_room_id = self.env.dbo_id
        elif self.env.dbo_id:
            self.room_id = self.env.dbo_id
        self.env.first_look(self)

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
        self.exit_msg = BroadcastMap(s="{n} expires, permanently.")
        for article in reversed(self.inven):
            article.current_slot = None
            article.drop(self)

        self.leave_env()
        self.status = 'dead'
        self.detach()

    @property
    def display_status(self):
        return {'status': self.status}

    @property
    def dead(self):
        return self.status == 'dead'
