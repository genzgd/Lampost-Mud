from lampost.context.resource import requires, m_requires
from lampost.datastore.dbo import RootDBO, DBORef
from lampost.env.movement import Direction
from lampost.model.mobile import MobileReset
from lampost.model.item import BaseItem
from lampost.model.article import ArticleReset

m_requires('log', __name__)

class Exit(RootDBO):
    dbo_fields = "dir_name",

    def __init__(self, direction=None, destination=None):
        self.direction = direction
        self.destination = destination

    @property
    def verbs(self):
        return (self.direction.key,), (self.direction.desc,)

    @property
    def dir_name(self):
        return self.direction.key

    @property
    def dir_desc(self):
        return self.direction.desc

    @dir_name.setter
    def dir_name(self, value):
        self.direction = Direction.ref_map[value]

    def rec_glance(self, source, **kwargs):
        if source.build_mode:
            source.display_line("{0}   {1}".format(self.direction.desc, self.destination.dbo_id))
        else:
            source.display_line(self.direction.desc)

    def __call__(self, source, **ignored):
        source.change_env(self.destination)
        return self.destination.rec_examine(source)


@requires('mud')
class Room(RootDBO):
    ROOM_COLOR = 0xAD419A
    ROOM_SEP = "-=" * 30
    EXIT_COLOR = 0x808000
    ITEM_COLOR = 0x7092BE

    dbo_key_type = "room"
    dbo_fields = "title", "desc", "dbo_rev"
    dbo_collections = DBORef("exits", Exit), DBORef("extras", BaseItem), DBORef("mobile_resets", MobileReset), \
        DBORef("article_resets", ArticleReset)

    dbo_rev = 0

    def __init__(self, dbo_id, title=None, desc=None):
        self.dbo_id = dbo_id
        self.title = title
        self.desc = desc
        self.contents = []
        self.exits = []
        self.mobile_resets = []
        self.article_resets = []
        self.extras = []

    @property
    def room_id(self):
        return self.dbo_id

    @property
    def area_id(self):
        return self.room_id.split(":")[0]

    def rec_glance(self, source, **ignored):
        return source.display_line(self.title, Room.ROOM_COLOR)

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
            source.display_line("{0} [{1}]".format(self.title, self.dbo_id), 0x6b306b)
        else:
            source.display_line(self.title)
        source.display_line(Room.ROOM_SEP, Room.ROOM_COLOR)
        source.display_line(self.desc, Room.ROOM_COLOR)
        source.display_line(Room.ROOM_SEP, Room.ROOM_COLOR)
        if self.exits:
            if source.build_mode:
                for my_exit in self.exits:
                    source.display_line("Exit: {0} {1} ".format(my_exit.dir_desc, my_exit.destination.dbo_id), Room.EXIT_COLOR)
            else:
                source.display_line("Obvious exits are: " + self.short_exits(),  Room.EXIT_COLOR)
        else:
            source.display_line("No obvious exits", Room.EXIT_COLOR)

        for obj in self.contents:
            if obj != source:
                obj.rec_glance(source)

    def short_exits(self):
        return ", ".join([ex.dir_desc for ex in self.exits])

    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit

    def tell_contents(self, msg_type,  *args):
        for receiver in self.contents:
            rec_method = getattr(receiver, msg_type, None)
            if rec_method:
                rec_method(*args)

    def reset(self):
        for m_reset in self.mobile_resets:
            template = self.mud.get_mobile(m_reset.mobile_id)
            if not template:
                error("Missing template for mobile reset roomId: {0}  mobileId: {1}".format(self.dbo_id, m_reset.mobile_id))
                continue
            curr_count = len([entity for entity in self.contents if getattr(entity, "mobile_id", None) == m_reset.mobile_id])
            for unused in range(m_reset.mob_count - curr_count):
                self.add_mobile(template, m_reset)
            if m_reset.mob_count <= curr_count < m_reset.mob_max:
                self.add_mobile(template, m_reset)
        for a_reset in self.article_resets:
            template = self.mud.get_article(a_reset.article_id)
            if not template:
                error('Invalid article in reset roomId: {0}  articleId: {1}'.format(self.dbo_id, a_reset.article_id))
                continue
            curr_count = len([entity for entity in self.contents if getattr(entity, "article_id", None) == a_reset.article_id])
            for unused in range(a_reset.article_count - curr_count):
                self.add_template(template)
            if a_reset.article_count <= curr_count < a_reset.article_max:
                self.add_template(template)

    def add_mobile(self, template, reset):
        instance = self.add_template(template)
        for article_load in reset.article_loads:
            article_template = self.mud.get_article(article_load.article_id)
            if not template:
                error("Invalid article load for roomId: {0}, mobileId: {1}, articleId: {2}".format(self.dbo_id, template.mobile_id, article_template.article_id))
                continue
            article = article_template.create_instance()
            instance.add_inven(article)
            if article_load.type == "equip":
                instance.equip_article(article)

    def add_template(self, template):
        instance = template.create_instance()
        instance.enter_env(self)
        return instance



Exit.dbo_refs = DBORef("destination", Room, "room"),