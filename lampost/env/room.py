from collections import defaultdict
import itertools
import random

from lampost.comm.broadcast import Broadcast
from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField
from lampost.datastore.dbo import RootDBO, DBOField, DBOTField
from lampost.env.movement import Direction
from lampost.gameops.script import Scriptable
from lampost.gameops.display import *
from lampost.mud.inventory import InvenContainer


m_requires(__name__, 'log', 'dispatcher', 'datastore')

default_room_size = 10
room_reset_time = 600


def tell(listeners, msg_type, *args):
    for listener in listeners:
        try:
            receiver = getattr(listener, msg_type)
        except AttributeError:
            continue
        receiver(*args)


class Exit(RootDBO):
    class_id = 'exit'

    target_class = None
    direction = DBOField(None, 'direction')
    destination = DBOField()
    desc = DBOField()
    aliases = DBOField([])

    can_follow = True
    msg_class = 'no_args'

    @property
    def verbs(self):
        return (self.direction.dbo_id,), (self.direction.desc,)

    @property
    def name(self):
        return self.direction.desc

    @property
    def from_name(self):
        return Direction.ref_map.get(self.direction.rev_key).desc

    @property
    def dest_room(self):
        return load_by_key('room', self.destination)

    def examine(self, source, **_):
        source.display_line('Exit: {}  {}'.format(self.direction.desc, self.dest_room.title), EXIT_DISPLAY)

    def __call__(self, source, **_):
        source.env.allow_leave(source, self)
        self._move_user(source)

    def _move_user(self, source):
        if source.instance:
            destination = source.instance.get_room(self.destination)
        else:
            destination = self.dest_room
        source.change_env(destination, self)


class Room(RootDBO, Scriptable):
    dbo_key_type = 'room'
    dbo_parent_type = 'area'
    dbo_key_sort = lambda key: int(key.split(":")[1])

    dbo_rev = DBOTField(0)
    desc = DBOTField()
    size = DBOTField(default_room_size)
    exits = DBOTField([], 'exit')
    extras = DBOTField([], 'base_item')
    mobile_resets = DBOTField([], 'mobile_reset')
    article_resets = DBOTField([], 'article_reset')
    features = DBOTField([], 'feature')
    title = DBOTField()
    instance_providers = AutoField([])

    instance = None

    _garbage_pulse = None

    def __init__(self, dbo_id=None):
        super().__init__(dbo_id)
        self.inven = InvenContainer()
        self.denizens = []
        self.mobiles = defaultdict(set)

    @property
    def action_providers(self):
        return itertools.chain(self.features, self.exits, self.denizens, self.inven, self.instance_providers)

    @property
    def name(self):
        if self.instance:
            return "{} (instance {})".format(self.title, self.instance.instance_id)
        return self.title

    @property
    def contents(self):
        return itertools.chain(self.features, self.denizens, self.inven)

    def glance(self, source, **_):
        return source.display_line(self.name, ROOM_DISPLAY)

    def entity_enters(self, entity, enter_action, entry_msg=None):
        self.receive_broadcast(entry_msg)
        entity.env = self
        self.denizens.append(entity)
        entity.pulse_stamp = current_pulse()
        tell(self.contents, "entity_enter_env", entity, enter_action)

    def entity_leaves(self, entity, exit_action, exit_msg=None):
        self.receive_broadcast(exit_msg)
        self.denizens.remove(entity)
        tell(self.contents, "entity_leave_env", entity, exit_action)

    def add_inven(self, article):
        self.inven.append(article)
        article.pulse_stamp = current_pulse()

    def remove_inven(self, article):
        self.inven.remove(article)

    def receive_broadcast(self, broadcast):
        if not broadcast:
            return
        if getattr(broadcast, 'target', None) == self:
            broadcast.target = None
        tell(self.contents, "receive_broadcast", broadcast)

    def broadcast(self, **kwargs):
        self.receive_broadcast(Broadcast(**kwargs))

    def first_look(self, source):
        self.examine(source)

    def examine(self, source, **_):
        source.display_line(self.name, ROOM_TITLE_DISPLAY)
        source.display_line('HRT', ROOM_DISPLAY)
        source.display_line(self.desc, ROOM_DISPLAY)
        source.display_line('HRB', ROOM_DISPLAY)
        if self.exits:
            for my_exit in self.exits:
                my_exit.examine(source)
        else:
            source.display_line("No obvious exits", EXIT_DISPLAY)
        tell([x for x in self.contents if x != source], 'glance', source)

    def short_exits(self):
        return ", ".join([ex.name for ex in self.exits])

    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit

    def on_loaded(self):
        if not self._garbage_pulse:
            self.reset()
            self._garbage_pulse = register_p(self.check_garbage, seconds=room_reset_time + 1)

    def allow_leave(self, *args):
        pass


    def check_garbage(self):
        if hasattr(self, 'dirty'):
            if not self.instance:
                save_object(self)
            del self.dirty
        stale_pulse = future_pulse(-room_reset_time)
        for obj in self.contents:
            obj_pulse = getattr(obj, 'pulse_stamp', 0)
            if obj_pulse > stale_pulse or hasattr(obj, 'is_player'):
                return
        self.clean_up()

    def reset(self):
        new_mobiles = defaultdict(list)
        for m_reset in self.mobile_resets:
            curr_count = len(self.mobiles[m_reset.mobile])
            for _ in range(m_reset.reset_count - curr_count):
                new_mobiles[m_reset.reset_key].append(m_reset.mobile.create_instance(self))
            if m_reset.reset_count <= curr_count < m_reset.reset_max:
                new_mobiles[m_reset.reset_key].append(m_reset.mobile.create_instance(self))

        for a_reset in self.article_resets:
            template = a_reset.article
            if a_reset.mobile_ref:
                for new_mobile in new_mobiles[a_reset.mobile_ref]:
                    quantity = random.randrange(a_reset.reset_count, a_reset.reset_max + 1)
                    if template.divisible:
                        article = template.create_instance(new_mobile)
                        article.quantity = quantity
                        new_mobile.add_inven(article)
                    else:
                        for _ in range(quantity):
                            article = template.create_instance(new_mobile)
                            new_mobile.add_inven(article)
                            if a_reset.load_type == 'equip':
                                new_mobile.equip_article(article)
            else:
                curr_count = len([entity for entity in self.inven if getattr(entity, 'template', None) == template])
                if template.divisible:
                    if not curr_count:
                        instance = template.create_instance(self)
                        instance.quantity = random.randrange(a_reset.reset_count, a_reset.reset_max + 1)
                        instance.enter_env(self)
                else:
                    for _ in range(a_reset.reset_count - curr_count):
                        template.create_instance(self).enter_env(self)
                    if a_reset.reset_count <= curr_count < a_reset.reset_max:
                        template.create_instance(self).enter_env(self)

    def social(self):
        pass

    def clean_up(self):
        if self._garbage_pulse:
            del self._garbage_pulse
        detach_events(self)
        for mobile_list in self.mobiles.values():
            for mobile in mobile_list:
                if mobile.env != self:
                    mobile.enter_env(self)
        for obj in self.contents:
            if hasattr(obj, 'detach'):
                obj.detach()
        if not getattr(self, 'template', None):
            evict_object(self)

    def reload(self):
        players = [denizen for denizen in self.denizens if hasattr(denizen, 'is_player')]
        for player in players:
            player.change_env(safe_room)
        self.clean_up()
        evict_object(self)
        new_room = load_by_key(self.dbo_key_type, self.dbo_id)
        if new_room:
            for player in players:
                player.change_env(new_room)


safe_room = Room('temp:safe')
safe_room.title = "Safe Room"
safe_room.desc = "A temporary safe room when room is being updated."
safe_room.first_look = lambda source: None
