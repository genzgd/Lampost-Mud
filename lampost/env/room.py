from lampost.context.resource import m_requires
from lampost.datastore.dbo import RootDBO, DBORef, DBOField
from lampost.env.movement import Direction
from lampost.model.mobile import MobileReset, MobileTemplate
from lampost.model.item import BaseDBO
from lampost.model.article import ArticleReset, ArticleTemplate
from lampost.gameops.display import *


m_requires('log', 'datastore', __name__)


class Exit(RootDBO):
    direction = DBORef(Direction)
    desc = DBOField()
    aliases = DBOField([])

    can_follow = True
    msg_class = 'no_args'

    def __init__(self, direction=None, destination=None):
        super(Exit, self).__init__()
        self.direction = direction
        self.destination = destination

    @property
    def verbs(self):
        return (self.direction.key,), (self.direction.desc,)

    @property
    def dir_desc(self):
        return self.direction.desc

    @property
    def from_desc(self):
        from_dir = Direction.ref_map.get(self.direction.rev_key, None)
        if from_dir:
            return from_dir.desc

    def rec_glance(self, source, **ignored):
        if source.build_mode:
            source.display_line("{0}   {1}".format(self.direction.desc, self.destination.dbo_id))
        else:
            source.display_line(self.direction.desc)

    def __call__(self, source, **ignored):
        source.change_env(self.destination, self)
        if getattr(source, 'session', None):
            return self.destination.rec_examine(source)


class Room(RootDBO):
    dbo_key_type = "room"

    dbo_rev = DBOField(0)
    desc = DBOField()
    size = DBOField(10)
    exits = DBOField([], Exit)
    extras = DBOField([], BaseDBO)
    mobile_resets = DBOField([], MobileReset)
    article_resets = DBOField([], ArticleReset)
    title = DBOField()

    def __init__(self, dbo_id, title=None, desc=None):
        super(Room, self).__init__(dbo_id)
        self.title = title
        self.desc = desc
        self.contents = []

    @property
    def dbo_set_key(self):
        return "area_rooms:{}".format(self.area_id)

    @property
    def room_id(self):
        return self.dbo_id

    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]

    def rec_glance(self, source, **ignored):
        return source.display_line(self.title, ROOM_DISPLAY)

    def rec_entity_enters(self, source):
        self.contents.append(source)
        self.tell_contents("rec_entity_enter_env", source)
        entry_msg = getattr(source, "entry_msg", None)
        if entry_msg:
            source.entry_msg.source = source
            self.rec_broadcast(entry_msg)

    def rec_entity_leaves(self, source):
        self.contents.remove(source)
        self.tell_contents("rec_entity_leave_env", source)
        exit_msg = getattr(source, "exit_msg", None)
        if exit_msg:
            source.exit_msg.source = source
            self.rec_broadcast(exit_msg)

    def rec_broadcast(self, broadcast):
        if not broadcast:
            return
        if getattr(broadcast, 'target', None) == self:
            broadcast.target = None
        self.tell_contents("rec_broadcast", broadcast)

    def rec_social(self):
        pass

    @property
    def elements(self):
        return self.contents + self.exits + self.extras

    def rec_examine(self, source, **ignored):
        if source.build_mode:
            source.display_line("{0} [{1}]".format(self.title, self.dbo_id), ROOM_TITLE_DISPLAY)
        else:
            source.display_line(self.title, ROOM_TITLE_DISPLAY)
        source.display_line('HRT', ROOM_DISPLAY)
        source.display_line(self.desc, ROOM_DISPLAY)
        source.display_line('HRB', ROOM_DISPLAY)
        if self.exits:
            if source.build_mode:
                for my_exit in self.exits:
                    source.display_line("Exit: {0} {1} ".format(my_exit.dir_desc, my_exit.destination.dbo_id), EXIT_DISPLAY)
            else:
                source.display_line("Obvious exits are: " + self.short_exits(), EXIT_DISPLAY)
        else:
            source.display_line("No obvious exits", EXIT_DISPLAY)

        for obj in self.contents:
            if obj != source:
                obj.rec_glance(source)

    def short_exits(self):
        return ", ".join([ex.dir_desc for ex in self.exits])

    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit

    # noinspection PyCallingNonCallable
    def tell_contents(self, msg_type, *args):
        for receiver in self.contents:
            try:
                getattr(receiver, msg_type)(*args)
            except AttributeError:
                pass

    def reset(self):
        for m_reset in self.mobile_resets:
            template = load_object(MobileTemplate, m_reset.mobile_id)
            if not template:
                error("Missing template for mobile reset roomId: {0}  mobileId: {1}".format(self.dbo_id, m_reset.mobile_id))
                continue
            curr_count = len([entity for entity in self.contents if getattr(entity, 'template', None) == template])
            for unused in range(m_reset.reset_count - curr_count):
                self.add_mobile(template, m_reset)
            if m_reset.reset_count <= curr_count < m_reset.reset_max:
                self.add_mobile(template, m_reset)
        for a_reset in self.article_resets:
            template = load_object(ArticleTemplate, a_reset.article_id)
            if not template:
                error('Invalid article in reset roomId: {0}  articleId: {1}'.format(self.dbo_id, a_reset.article_id))
                continue
            curr_count = len([entity for entity in self.contents if getattr(entity, 'template', None) == template])
            for unused in range(a_reset.reset_count - curr_count):
                self.add_template(template)
            if a_reset.reset_count <= curr_count < a_reset.reset_max:
                self.add_template(template)

    def add_mobile(self, template, reset):
        instance = self.add_template(template)
        for article_load in reset.article_loads:
            article_template = load_object(ArticleTemplate, article_load.article_id)
            if not template:
                error(
                    "Invalid article load for roomId: {0}, mobileId: {1}, articleId: {2}".format(self.dbo_id, template.mobile_id, article_template.article_id))
                continue
            article = article_template.create_instance()
            instance.add_inven(article)
            if article_load.load_type == "equip":
                instance.equip_article(article)

    def add_template(self, template):
        instance = template.create_instance()
        instance.enter_env(self)
        return instance

dest_ref = DBORef(Room)
Exit.destination = dest_ref
dest_ref.dbo_init(Exit, 'destination')
Exit.dbo_fields.add('destination')
