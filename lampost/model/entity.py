import math

from lampost.comm.broadcast import Broadcast
from lampost.context.resource import m_requires
from lampost.model.item import BaseItem

m_requires('log', __name__)

class Entity(BaseItem):
    env = None
    entry_msg = Broadcast(s="{n} arrives.")
    exit_msg = Broadcast(s="{n} leaves.")
    current_target = None

    def baptise(self, soul):
        self.registrations = set()
        self.soul = soul
        self.target_map = {}
        self.target_key_map = {}
        self.actions = {}
        self.target_map[self] = []
        self.add_target_keys([self.target_id], self)
        self.add_actions(soul)

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
        return Broadcast(s="You pick up {N}", e="{n} picks up {N}", target=article, source=self)

    def drop_inven(self, article):
        if not article in self.inven:
            return "You don't have that."
        self.inven.remove(article)
        self.remove_action(article)
        self.remove_target(article)
        article.enter_env(self.env)
        return Broadcast(s="You drop {N}", e="{n} drops {N}", target=article, source=self)

    def enhance_soul(self, actions):
        self.add_actions(actions)
        self.soul.update(set(actions))

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
        if self.target_map.get(target):  #Should not happen
            error("Trying to add " + unicode(target_id) + " more than once")
            return
        self.target_map[target] = []
        self.add_target_key_set(target, target_id, parent)
        for target_id in getattr(target, "target_aliases", []):
            self.add_target_key_set(target, target_id, parent)

    def add_target_key_set(self, target, target_id, parent):
        if parent == self.env:
            prefix = "the",
        elif parent == self.inven:
            prefix = "my",
        else:
            prefix = ()
        target_keys = list(self.gen_ids(prefix + target_id))
        self.add_target_keys(target_keys, target)


    def add_target_keys(self, target_keys, target):
        for target_key in target_keys:
            self.target_map[target].append(target_key)
            key_data = self.target_key_map.get(target_key)
            if key_data:
                key_data.append(target)
                new_count = len(key_data)
                if new_count == 2:
                    self.target_key_map[target_key + ("1",)] = [key_data[0]]
                self.target_key_map[target_key + (unicode(new_count),)] = [target]
            else:
                self.target_key_map[target_key] = [target]


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
        for target_key in target_keys:
            key_data = self.target_key_map[target_key]
            if len(key_data) == 1:
                del self.target_key_map[target_key]
            else:
                target_loc = key_data.index(target)
                key_data.pop(target_loc)
                self.renumber_keys(target_key, key_data)


    def renumber_keys(self, target_key, key_data):
        for ix in range(len(key_data) + 1):
            number_key = target_key + (unicode(ix + 1),)
            del self.target_key_map[number_key]
        if len(key_data) < 2:
            return
        for ix, target in enumerate(key_data):
            self.target_key_map[target_key + (unicode(ix + 1),)] = [target]


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
            bucket = self.actions.get(verb, None)
            if bucket:
                bucket.remove(action)
                if len(bucket) == 0:
                    del self.actions[verb]
            else:
                error("Removing action " + unicode(verb) + " that does not exist from " + self.short_desc(self))
        for sub_action in getattr(action, "sub_providers", []):
            self.remove_action(sub_action)

    def parse_command(self, command):
        words = command.lower().split()
        matches = list(self.match_actions(words))
        if not matches:
            return None, None
        if len(matches) > 1:
            return matches, None
        action, verb, args, target, target_method, obj, obj_method = matches[0]
        return matches, action(source=self, target=target, verb=verb, args=args,
            target_method=target_method, command=command, obj=obj, obj_method=obj_method)


    def match_actions(self, words):
        for verb_size in range(1, len(words) + 1):
            verb = tuple(words[:verb_size])
            args = words[verb_size:]
            for action in self.actions.get(verb, []):
                msg_class = getattr(action, "msg_class", None)
                if not msg_class:
                    yield action, verb, tuple(args), action, None, None, None
                    continue
                if getattr(action, 'prep', None):
                    try:
                        prep_loc = args.index(action.prep)
                    except ValueError:
                        continue
                    obj_args = tuple(args[(prep_loc + 1):])
                    args = tuple(args[:prep_loc])
                    obj_msg_class = getattr(action, "obj_msg_class", None)
                else:
                    args = tuple(args)
                    obj_args = None
                fixed_targets = getattr(action, "fixed_targets", None)
                for target, target_method in self.matching_targets(args, msg_class):
                    if not fixed_targets or target in fixed_targets:
                        if obj_args:
                            if not obj_msg_class:
                                yield action, verb, args, target, target_method, obj_args, None
                                continue
                            for obj, obj_method in self.matching_targets(args, obj_msg_class):
                                yield action, verb, args, target, target_method, obj, obj_method
                        else:
                            yield action, verb, args, target, target_method, None, None

    def matching_targets(self, target_args, msg_class):
        target_list = self.target_key_map.get(target_args, []) if target_args else [self.env]
        for target in target_list:
            target_method = getattr(target, msg_class, None)
            if target_method:
                yield target, target_method
                return

    def change_env(self, new_env):
        self.leave_env()
        self.enter_env(new_env)

    def leave_env(self):
        if self.env:
            self.remove_actions(self.env.elements)
            self.remove_target(self.env)
            self.remove_targets(self.env.elements)
            self.env.rec_entity_leaves(self)

    def enter_env(self, new_env):
        self.env = new_env
        self.room_id = new_env.room_id
        self.add_actions(self.env.elements)
        self.add_target(new_env)
        self.add_targets(new_env.elements, new_env)
        self.env.rec_entity_enters(self)

    def broadcast(self, broadcast):
        pass
