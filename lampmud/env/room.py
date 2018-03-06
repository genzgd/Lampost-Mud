import itertools
import random
from collections import defaultdict

from lampost.di.app import on_app_start
from lampost.di.config import on_config_change, config_value
from lampost.di.resource import Injected, module_inject
from lampost.event.zone import Attachable
from lampost.gameops.action import ActionCache
from lampost.meta.auto import AutoField
from lampost.db.dbo import ChildDBO, PropertyDBO
from lampost.db.dbofield import DBOField, DBOCField, DBOLField
from lampost.gameops.script import Scriptable, Shadow
from lampost.util.classes import call_each

from lampmud.comm.broadcast import Broadcast
from lampmud.env.movement import Direction

log = Injected('log')
ev = Injected('dispatcher')
db = Injected('datastore')
module_inject(__name__)


@on_app_start
@on_config_change
def _config():
    global room_reset_time
    room_reset_time = config_value('room_reset_time')


class Exit(PropertyDBO):
    class_id = 'exit'

    destination = DBOLField(dbo_class_id='room', required=True)
    direction = DBOField()
    desc = DBOField()
    aliases = DBOField([])
    match_args = 'source',

    can_follow = True

    @property
    def verbs(self):
        return self._dir.dbo_id, self._dir.desc

    @property
    def name(self):
        return self._dir.desc

    @property
    def from_name(self):
        return Direction.ref_map.get(self._dir.rev_key).desc

    def _on_hydrated(self):
        self._dir = Direction.ref_map.get(self.direction)

    def examine(self, source):
        source.display_line('Exit: {}  {}'.format(self._dir.desc, self.destination.title), 'exit')

    def __call__(self, source):
        source.env.allow_leave(source, self)
        self._move_user(source)

    def _move_user(self, source):
        if source.instance:
            destination = source.instance.get_room(self.destination)
        else:
            destination = self.destination
        source.change_env(destination, self)


class Room(ChildDBO, Attachable, Scriptable):
    dbo_key_type = 'room'
    dbo_parent_type = 'area'

    @staticmethod
    def dbo_key_sort(key):
        return int(key.split(':')[1])

    desc = DBOCField()
    size = DBOCField(10)
    exits = DBOCField([], 'exit')
    extras = DBOCField([], 'base_item')
    mobile_resets = DBOCField([], 'mobile_reset')
    article_resets = DBOCField([], 'article_reset')
    features = DBOCField([], 'untyped')
    title = DBOCField()
    flags = DBOField({})
    instance_providers = AutoField([])
    denizens = AutoField(set())
    current_actions = AutoField(ActionCache())

    instance = None

    _garbage_pulse = None

    def _on_updated(self):
        if self.attached:
            call_each(list(self.contents), 'attach')

    def _on_attach(self):
        self.inven = []
        self.mobiles = defaultdict(set)
        call_each(list(self.contents), 'attach')
        self._garbage_pulse = ev.register_p(self.check_garbage, seconds=room_reset_time + 1)
        self._refresh_contents()

    def _on_detach(self):
        for mobile_list in self.mobiles.values():
            for mobile in mobile_list:
                if mobile.env != self:
                    mobile.change_env(self)
        call_each(list(self.contents), 'detach')
        del self._garbage_pulse
        del self.current_actions
        del self.denizens

    def _refresh_contents(self):
        self.current_actions = ActionCache().add(self.instance_providers, self.features, self.exits,
                                                 self.inven, self.denizens)
        self.reset()

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
        return itertools.chain(self.features, self.denizens, self.inven, self.exits)

    @Shadow
    def long_desc(self):
        return self.desc

    @Shadow
    def glance(self, source, **_):
        return source.display_line(self.name, 'room')

    @Shadow
    def entity_enters(self, entity, enter_action, entry_msg=None):
        self.attach()
        self.receive_broadcast(entry_msg)
        entity.env = self
        self.denizens.add(entity)
        entity.pulse_stamp = ev.current_pulse
        self.current_actions.add(entity)
        call_each(self.contents, "entity_enter_env", entity, enter_action)

    def entity_leaves(self, entity, exit_action, exit_msg=None):
        self.receive_broadcast(exit_msg)
        self.denizens.remove(entity)
        self.current_actions.remove(entity)
        call_each(self.contents, "entity_leave_env", entity, exit_action)

    @Shadow
    def add_inven(self, article):
        self.inven.append(article)
        self.current_actions.add(article)
        article.pulse_stamp = ev.current_pulse

    def remove_inven(self, article):
        self.inven.remove(article)
        self.current_actions.remove(article)

    @Shadow
    def receive_broadcast(self, broadcast, **_):
        if not broadcast:
            return
        if getattr(broadcast, 'target', None) == self:
            broadcast.target = None
        call_each(self.contents, "receive_broadcast", broadcast)

    def broadcast(self, **kwargs):
        self.receive_broadcast(Broadcast(**kwargs))

    def first_look(self, source):
        self.examine(source)

    @Shadow
    def examine(self, source):
        source.display_line(self.name, 'room_title')
        source.display_line('HRT', 'room')
        source.display_line(self.long_desc(), 'room')
        source.display_line('HRB', 'room')
        if self.exits:
            for my_exit in self.exits:
                my_exit.examine(source)
        else:
            source.display_line("No obvious exits", 'exit')
        call_each([x for x in self.contents if x != source], 'glance', source)

    def short_exits(self):
        return ", ".join([ex.name for ex in self.exits])

    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit

    @Shadow
    def allow_leave(self, source, leave_exit):
        pass

    def check_garbage(self):
        if hasattr(self, 'dirty'):
            if not self.instance:
                db.save_object(self)
            del self.dirty
        stale_pulse = ev.future_pulse(room_reset_time)
        for obj in self.contents:
            obj_pulse = getattr(obj, 'pulse_stamp', 0)
            if obj_pulse > stale_pulse or hasattr(obj, 'is_player'):
                return
        self.detach()

    @Shadow
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
                        instance.quantity = random.randrange(a_reset.reset_count, max(a_reset.reset_max, a_reset.reset_count) + 1)
                        instance.enter_env(self)
                else:
                    for _ in range(a_reset.reset_count - curr_count):
                        template.create_instance(self).enter_env(self)
                    if a_reset.reset_count <= curr_count < a_reset.reset_max:
                        template.create_instance(self).enter_env(self)

    def social(self):
        pass
