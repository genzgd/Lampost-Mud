import math

from collections import defaultdict
from lampost.gameops.action import action_handler

from lampost.comm.broadcast import Broadcast, SingleBroadcast
from lampost.context.resource import m_requires
from lampost.gameops.parser import ParseError, find_actions, parse_actions, has_action, \
    MISSING_VERB, MISSING_TARGET
from lampost.model.item import BaseItem

m_requires('log', __name__)


def enhance_soul(owner, action):
    for verb in action.verbs:
        owner.soul[verb].add(action)


def diminish_soul(owner, action):
    for verb in action.verbs:
        verb_set = owner.soul.get(verb)
        if verb_set:
            verb_set.remove(action)
            if not verb_set:
                del owner.soul[verb]
        else:
            debug("Trying to remove non-existent {} from {} soul".format(verb, owner.name))


class Entity(BaseItem):
    template_fields = "size", "sex"

    sex = 'none'
    size = 'medium'

    status = 'awake'
    living = True
    combat = False

    entry_msg = Broadcast(e='{n} materializes.', ea="{n} arrives from the {N}.", silent=True)
    exit_msg = Broadcast(e='{n} dematerializes.', ea="{n} leaves to the {N}", silent=True)

    def __init__(self):
        self.soul = defaultdict(set)
        self.followers = set()
        self.registrations = set()
        self.target_map = {}
        self.target_key_map = {}
        self.actions = {}
        self.target_map[self] = {}

    def baptise(self):
        self.add_target_keys([self.target_id, ('self',)], self, self.target_map[self])

    def equip(self, inven):
        self.inven = inven
        self.add_actions(inven)
        self.add_targets(inven, inven)

    def add_inven(self, article):
        if article in self.inven:
            return "You already have that."
        article.leave_env()
        self.inven.add(article)
        self.add_action(article)
        self.add_target(article, self.inven)
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
        self.add_target(entity)
        self.add_action(entity)

    def rec_entity_leave_env(self, entity):
        self.remove_target(entity)
        self.remove_action(entity)

    def add_targets(self, targets, parent=None):
        for target in targets:
            self.add_target(target, parent)

    def add_target(self, target, parent=None):
        if target == self:
            return
        try:
            target_id = target.target_id
        except AttributeError:
            return
        if self.target_map.get(target):
            error("Trying to add " + target_id + " more than once")
            return
        target_entry = {}
        self.add_target_key_set(target, target_entry, target_id, parent)
        for target_id in getattr(target, "target_aliases", []):
            self.add_target_key_set(target, target_entry, target_id, parent)
        self.target_map[target] = target_entry

    def add_target_key_set(self, target, target_entry, target_id, parent):
        if parent == self.env:
            prefix = unicode("the"),
        elif parent == self.inven:
            prefix = unicode("my"),
        else:
            prefix = ()
        target_keys = self.gen_ids(prefix + target_id)
        self.add_target_keys(target_keys, target, target_entry)

    def add_target_keys(self, target_keys, target, target_entry):
        for target_key in target_keys:
            current_key = target_key
            key_count = 1
            while self.target_key_map.get(current_key):
                key_count += 1
                current_key = target_key + (unicode(key_count),)
            self.target_key_map[current_key] = target
            target_entry[target_key] = key_count

    def gen_ids(self, target_id):
        prefix_count = len(target_id) - 1
        target = target_id[prefix_count],
        for x in range(0, int(math.pow(2, prefix_count))):
            next_prefix = []
            for y in range(0, prefix_count):
                if int(math.pow(2, y)) & x:
                    next_prefix.append(target_id[y])
            yield tuple(next_prefix) + target

    def remove_targets(self, targets):
        for target in targets:
            self.remove_target(target)

    def remove_target(self, target):
        if self == target:
            return
        target_keys = self.target_map.get(target, None)
        if not target_keys:
            return
        del self.target_map[target]
        for target_key, key_count in target_keys.iteritems():
            if key_count > 1:
                prev_key = target_key + (unicode(key_count),)
            else:
                prev_key = target_key
            del self.target_key_map[prev_key]
            key_count += 1
            next_key = target_key + (unicode(key_count),)
            next_target = self.target_key_map.get(next_key)
            while next_target:
                self.target_key_map[prev_key] = next_target
                self.target_map[next_target][target_key] = key_count - 1
                del self.target_key_map[next_key]
                prev_key = next_key
                key_count += 1
                next_key = target_key + (unicode(key_count),)
                next_target = self.target_key_map.get(next_key)

    def add_actions(self, actions):
        for action in actions:
            self.add_action(action)

    def add_action(self, action):
        for verb in getattr(action, "verbs", []):
            bucket = self.actions.get(verb)
            if not bucket:
                bucket = set()
                self.actions[verb] = bucket
            bucket.add(action)
        for sub_action in getattr(action, "sub_actions", []):
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
        for sub_action in getattr(action, "sub_providers", []):
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
            self.remove_actions(self.env.elements)
            self.remove_target(self.env)
            self.remove_targets(self.env.elements)
            try:
                self.exit_msg.target = ex.dir_desc
            except AttributeError:
                self.exit_msg.target = None
            self.env.rec_entity_leaves(self)

    def enter_env(self, new_env, ex=None):
        self.env = new_env
        self.room_id = new_env.room_id
        self.add_actions(new_env.elements)
        self.add_target(new_env)
        self.add_targets(new_env.elements, new_env)
        try:
            self.entry_msg.target = ex.from_desc
        except AttributeError:
            self.entry_msg.target = None
        self.env.rec_entity_enters(self)

    def broadcast(self, broadcast=None, **kwargs):
        if isinstance(broadcast, basestring):
            broadcast = SingleBroadcast(broadcast, display)
        elif not broadcast:
            broadcast = Broadcast(**kwargs)
        broadcast.source = self
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
            self.drop_inven(article)
        self.leave_env()
        self.status = 'dead'
        self.detach()

    def detach(self):
        for follower in self.followers:
            del follower.following
            follower.display_line("You are no longer following {}.".format(self.name))
        if hasattr(self, 'following'):
            self.following.display_line("{} is no longer following you.".format(self.name))
            del self.following
        super(Entity, self).detach()

    def equip_article(self, article):
        pass

    @property
    def display_status(self):
        return {'status': self.status}

    @property
    def dead(self):
        return self.status == 'dead'
