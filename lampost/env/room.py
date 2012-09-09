'''
Created on Feb 26, 2012

@author: Geoff
'''
from lampost.dto.display import Display, DisplayLine
from lampost.datastore.dbo import RootDBO, DBORef
from lampost.env.movement import Direction
from lampost.mobile.mobile import MobileReset
from lampost.model.item import BaseItem
from lampost.model.article import ArticleReset


class Exit(RootDBO):
    dbo_fields = "dir_name",

    def __init__(self, direction=None, destination=None):
        self.direction = direction
        self.destination = destination

    @property
    def verbs(self):
        return ((self.direction.key,), (self.direction.desc,))

    @property
    def dir_name(self):
        return self.direction.key

    @dir_name.setter
    def dir_name(self, value):
        self.direction = Direction.ref_map[value]

    def short_desc(self, observer=None):
        if observer and observer.build_mode:
            return "{0}   {1}".format(self.direction.desc, self.destination.dbo_id)
        else:
            return self.direction.desc

    def execute(self, source, **ignored):
        source.change_env(self.destination)
        return self.destination.rec_examine(source)


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
        return Display(self.short_desc(source), Room.ROOM_COLOR)

    def rec_examine(self, source, **ignored):
        return self.long_desc(source)

    def rec_entity_enters(self, source):
        self.contents.append(source)
        self.tell_contents("rec_entity_enter_env", source, source)
        entry_msg = getattr(source, "entry_msg", None)
        if entry_msg:
            source.entry_msg.source = source
            self.rec_broadcast(entry_msg, source)

    def rec_entity_leaves(self, source):
        self.contents.remove(source)
        self.tell_contents("rec_entity_leave_env", source, source)
        exit_msg = getattr(source, "exit_msg", None)
        if exit_msg:
            source.exit_msg.source = source
            self.rec_broadcast(exit_msg, source)

    def rec_broadcast(self, broadcast, exclude=None):
        if not broadcast:
            return
        if broadcast.target == self:
            broadcast.target = None
        self.tell_contents("rec_broadcast", exclude, broadcast)

    def rec_social(self):
        pass

    @property
    def children(self):
        return self.contents + self.exits + self.extras

    def long_desc(self, observer):
        short_desc = self.short_desc(observer)
        if observer and observer.build_mode:
            short_desc = "{0} [{1}]".format(short_desc, self.dbo_id)
        longdesc = Display(short_desc, 0x6b306b)
        longdesc.append(DisplayLine(Room.ROOM_SEP, Room.ROOM_COLOR))
        longdesc.append(DisplayLine(self.desc, Room.ROOM_COLOR))
        longdesc.append(DisplayLine(Room.ROOM_SEP, Room.ROOM_COLOR))
        if self.exits:
            if observer.build_mode:
                for my_exit in self.exits:
                    longdesc.append(DisplayLine("Exit: {0} ".format(my_exit.short_desc(observer)), Room.EXIT_COLOR))
            else:
                longdesc.append(DisplayLine("Obvious exits are: " + self.short_exits(),  Room.EXIT_COLOR))
        else:
            longdesc.append(DisplayLine("No obvious exits", Room.EXIT_COLOR))

        for obj in self.contents:
            if obj != observer:
                longdesc.append(DisplayLine(obj.short_desc(observer), Room.ITEM_COLOR))
        return longdesc

    def short_desc(self, observer):
        return self.title

    def short_exits(self):
        return ", ".join([ex.short_desc() for ex in self.exits])

    def find_exit(self, exit_dir):
        for my_exit in self.exits:
            if my_exit.direction == exit_dir:
                return my_exit

    def tell_contents(self, msg_type, exclude, *args):
        for receiver in self.contents:
            if receiver == exclude:
                continue
            rec_method = getattr(receiver, msg_type, None)
            if rec_method:
                rec_method(*args)

    def reset(self, area):
        for m_reset in self.mobile_resets:
            curr_count = len([entity for entity in self.contents if getattr(entity, "mobile_id", None) == m_reset.mobile_id])
            for unused in range(m_reset.mob_count - curr_count):
                area.create_mob(m_reset.mobile_id, self)
            if curr_count >= m_reset.mob_count and curr_count < m_reset.mob_max:
                area.create_mob(m_reset.mobile_id, self)
        for a_reset in self.article_resets:
            curr_count = len([entity for entity in self.contents if getattr(entity, "article_id", None) == a_reset.article_id])
            for unused in range(a_reset.article_count - curr_count):
                area.create_article(a_reset.article_id, self)
            if curr_count >= a_reset.article_count and curr_count < a_reset.article_max:
                area.create_article(a_reset.article_id, self)

    def refresh(self):
        for entity in self.contents:
            try:
                entity.refresh_env()
            except AttributeError:
                pass


Exit.dbo_refs = DBORef("destination", Room, "room"),