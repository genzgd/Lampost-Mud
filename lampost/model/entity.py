from collections import defaultdict
from operator import itemgetter
from lampost.datastore.dbo import DBOField
from lampost.gameops.action import action_handler

from lampost.comm.broadcast import Broadcast
from lampost.context.resource import m_requires
from lampost.gameops.parser import ParseError, find_actions, parse_actions, has_action, \
    MISSING_VERB, MISSING_TARGET
from lampost.model.item import BaseItem

m_requires('log', __name__)


class Entity(BaseItem):
    size = DBOField('medium')

    status = 'ok'
    living = True
    combat = False

    entry_msg = Broadcast(e='{n} materializes.', ea="{n} arrives from the {N}.", silent=True)
    exit_msg = Broadcast(e='{n} dematerializes.', ea="{n} leaves to the {N}", silent=True)

    def __init__(self, dbo_id=None):
        super(Entity, self).__init__(dbo_id)
        self._target_order = 0
        self._target_data = defaultdict(list)
        self.soul = defaultdict(set)
        self.followers = set()
        self.registrations = set()
        self.target_key_map = {}
        self.actions = {}
        self.local_actions = set()

    def baptise(self):
        for target_key in self.target_keys | {(unicode('self'),)}:
            self._target_data[target_key] = [(self, 0, 0)]
            self.target_key_map[target_key] = self
        self.add_actions(self.inven)
        self.add_targets(self.inven, 10)

    def enhance_soul(self, action):
        for verb in action.verbs:
            self.soul[verb].add(action)

    def diminish_soul(self, action):
        for verb in action.verbs:
            verb_set = self.soul.get(verb)
            if verb_set:
                verb_set.remove(action)
                if not verb_set:
                    del self.soul[verb]
            else:
                debug("Trying to remove non-existent {} from {} soul".format(verb, self.name))

    def add_inven(self, article):
        if article in self.inven:
            return "You already have that."
        article.leave_env()
        self.inven.add(article)
        self.add_action(article)
        self.add_target(article, 10)
        self.broadcast(s="You pick up {N}", e="{n} picks up {N}", target=article)

    def drop_inven(self, article):
        if not article in self.inven:
            return "You don't have that."
        self.inven.remove(article)
        self.remove_action(article)
        self.remove_target(article)
        article.enter_env(self.env)
        self.broadcast(s="You drop {N}", e="{n} drops {N}", target=article)

    def rec_entity_enter_env(self, entity):
        self.add_target(entity, 30)
        self.add_action(entity)

    def rec_entity_leave_env(self, entity, ex):
        self.remove_target(entity)
        self.remove_action(entity)

    def add_targets(self, targets, parse_priority):
        for target in targets:
            self.add_target(target, parse_priority)

    def add_target(self, target, parse_priority):
        if target == self:
            return
        self._target_order += 1
        try:
            target_keys = target.target_keys
        except AttributeError:
            return
        self.clear_target_keys(target_keys)
        for target_key in target_keys:
            existing_targets = self._target_data[target_key]
            existing_targets.append((target, parse_priority, self._target_order))
            existing_targets.sort(key=itemgetter(1, 2))
        self.update_target_keys(target_keys)
        self.on_target_added(target)
        self.add_targets(getattr(target, 'target_providers', []), parse_priority)

    def on_target_added(self, target):
        pass

    def clear_target_keys(self, target_keys):
        for target_key in target_keys:
            existing_targets = self._target_data.get(target_key, None)
            if existing_targets:
                del self.target_key_map[target_key]
                for key_count in range(1, len(existing_targets)):
                    del self.target_key_map[target_key + (unicode(key_count + 1),)]

    def update_target_keys(self, target_keys):
        for target_key in target_keys:
            self.update_target_key(target_key, self._target_data[target_key])

    def update_target_key(self, target_key, target_list):
        self.target_key_map[target_key] = target_list[0][0]
        for key_count in range(1, len(target_list)):
            self.target_key_map[target_key + (unicode(key_count + 1),)] = target_list[key_count][0]

    def remove_targets(self, targets):
        for target in targets:
            self.remove_target(target)

    def remove_target(self, target):
        if self == target:
            return
        try:
            target_keys = target.target_keys
        except AttributeError:
            return
        self.clear_target_keys(target_keys)
        for target_key in target_keys:
            existing_targets = self._target_data[target_key]
            remaining_targets = [existing_target for existing_target in existing_targets if existing_target[0] != target]
            if remaining_targets:
                self._target_data[target_key] = remaining_targets
                self.update_target_key(target_key, remaining_targets)
            else:
                del self._target_data[target_key]
        self.remove_targets(getattr(target, 'target_providers', []))

    def add_actions(self, actions):
        for action in actions:
            self.add_action(action)

    def add_action(self, action):
        if action == self:
            return
        for verb in getattr(action, "verbs", []):
            bucket = self.actions.get(verb)
            if not bucket:
                bucket = set()
                self.actions[verb] = bucket
            bucket.add(action)
        for sub_action in getattr(action, "action_providers", []):
            self.add_action(sub_action)

    def remove_actions(self, actions):
        for action in actions:
            self.remove_action(action)

    def remove_action(self, action):
        for verb in getattr(action, "verbs", []):
            try:
                bucket = self.actions[verb]
                bucket.remove(action)
                if not bucket:
                    del self.actions[verb]
            except KeyError:
                error("Removing action {} that does not exist from {}".format(verb, self.name))
        for sub_action in getattr(action, "action_providers", []):
            self.remove_action(sub_action)

    def parse(self, command):
        actions = find_actions(self, command)
        actions = self.filter_actions(actions)
        try:
            action, act_args = parse_actions(self, actions)
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
        if error.error_code in (MISSING_VERB, MISSING_TARGET):
            self.parse('say {}'.format(command))
        else:
            self.display_line(error.message)

    def rec_social(self, **ignored):
        pass

    def rec_follow(self, source, **ignored):
        self.followers.add(source)
        source.broadcast(s="You start following {N}.", t="{n} starts following you.", e="{n} starts following {N}.", target=self)

    def rec_examine(self, source, **ignored):
        super(Entity, self).rec_examine(source, **ignored)
        source.display_line("{0} is carrying:".format(self.name))
        if self.inven:
            for article in self.inven:
                article.rec_glance(source)
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
            old_env.rec_entity_leaves(self, ex)
            self.remove_actions(old_env.elements)
            self.remove_targets(old_env.elements)

    def enter_env(self, new_env, ex=None):
        self.env = new_env
        self.room_id = new_env.room_id
        new_env.rec_examine(self)
        self.entry_msg.target = getattr(ex, 'from_desc', None)
        self.env.rec_entity_enters(self)
        self.add_actions(new_env.elements)
        self.add_targets(new_env.elements, 30)

    def broadcast(self, **kwargs):
        broadcast = Broadcast(**kwargs)
        broadcast.source = self
        if self.env:
            self.env.rec_broadcast(broadcast)

    def display_line(self, line, display='default'):
        pass

    def output(self, response):
        pass

    def update_score(self):
        pass

    def can_see(self, target):
        return True

    def check_inven(self, article):
        pass

    def die(self):
        self.exit_msg = Broadcast(s="{n} expires, permanently.")
        for article in self.inven.copy():
            article.current_slot = None
            self.drop_inven(article)
        self.leave_env()
        self.status = 'dead'
        self.detach()

    def detach(self):
        super(Entity, self).detach()
        for follower in self.followers:
            del follower.following
            follower.display_line("You are no longer following {}.".format(self.name))
        if hasattr(self, 'following'):
            self.following.display_line("{} is no longer following you.".format(self.name))
            del self.following
        self._target_data.clear()
        self.target_key_map.clear()
        self.actions.clear()
        self.equip_slots.clear()

    def equip_article(self, article):
        pass

    @property
    def display_status(self):
        return {'status': self.status}

    @property
    def dead(self):
        return self.status == 'dead'
