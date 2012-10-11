from twisted.web.resource import Resource

from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO
from lampost.env.movement import Direction
from lampost.env.room import Room, Exit
from lampost.mobile.mobile import MobileReset
from lampost.model.article import ArticleReset
from lampost.model.item import BaseItem
from lampost.util.lmutil import DataError

m_requires('datastore', 'perm', 'mud', __name__)

class RoomResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', RoomList())
        self.putChild('get', RoomGet())
        self.putChild('create', RoomCreate())
        self.putChild('delete', RoomDelete())
        self.putChild('update', RoomUpdate())
        self.putChild('visit', RoomVisit())
        self.putChild('dir_list', DirList())
        self.putChild('create_exit', CreateExit())
        self.putChild('delete_exit', DeleteExit())

class DirList(Resource):
    @request
    def render_POST(self, content, session):
        return [{'key':dir.key, 'name':dir.desc} for dir in Direction.ordered]


class RoomList(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        if not area:
            raise DataError("Missing Area")
        return [RoomStubDTO(room) for room in area.rooms.values()]


class RoomGet(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.room_id, session)
        return RoomDTO(area, room)


class RoomCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        check_perm(session, area)
        room_dto = content.room
        room_id = content.area_id + ':'+ str(room_dto['id'])
        if area.get_room(room_id):
            raise DataError("ROOM_EXISTS")
        room = Room(room_id, room_dto['title'], room_dto['desc'])
        save_object(room)
        area.rooms.append(room)
        area.inc_next_room(room_dto['id'])
        save_object(area)
        return RootDTO(next_room_id=area.next_room_id, room=RoomStubDTO(room))

class RoomDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.room_id, session)
        main_contents = save_contents(room)
        deleted_exits = []
        for my_exit in room.exits:
            other_room = my_exit.destination
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_contents = save_contents(other_room)
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    restore_contents(other_room, other_contents)
                    deleted_exits.append(ExitDTO(other_exit, other_room.dbo_id))
        delete_object(room)
        area.rooms.remove(room)
        save_object(area, True)
        for entity in main_contents:
            if entity.dbo_key_type == 'player':
                mud.start_player(entity)
            else:
                entity.detach()
        return deleted_exits

class RoomVisit(Resource):
    @request
    def render_POST(self, content, session):
        room = mud.find_room(content.room_id)
        if not Room:
            raise DataError("ROOM_MISSING")
        session.player.change_env(room)
        session.append(session.player.parse('look'))

class RoomUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.id, session)
        contents = save_contents(room)
        room.title = content.title
        room.desc = content.desc
        room.extras = []
        for extra_json in content.extras:
            if extra_json.get('title', None):
                extra = BaseItem()
                load_json(extra, extra_json)
                room.extras.append(extra)
        room.mobile_resets = []
        for mobile_json in content.mobiles:
            mobile_reset = MobileReset()
            load_json(mobile_reset, mobile_json)
            room.mobile_resets.append(mobile_reset)
        room.article_resets = []
        for article_json in content.articles:
            article_reset = ArticleReset()
            load_json(article_reset, article_json)
            room.article_resets.append(article_reset)
        save_object(room, True)
        restore_contents(room, contents)
        return RoomDTO(area, room)

class CreateExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.start_room, session)
        new_dir = Direction.ref_map[content.direction]
        rev_dir = new_dir.rev_dir
        other_id = content.dest_area + ':' + str(content.dest_id)
        if room.find_exit(new_dir):
            raise DataError("Room already has " + new_dir.key + " exit.")

        if content.is_new:
            if area.get_room(other_id):
                raise DataError("Room " + other_id + " already exists")
            other_room = Room(other_id, content.dest_title, content.dest_title)
        else:
            other_area, other_room = get_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.key + " exit.")

        contents = save_contents(room)
        this_exit = Exit(new_dir, other_room)
        room.exits.append(this_exit)
        save_object(room, True)
        restore_contents(room, contents)

        result = RootDTO()
        if not content.one_way:
            contents = save_contents(other_room)
            other_exit = Exit(rev_dir, room)
            other_room.exits.append(other_exit)
            restore_contents(other_room, contents)
            result.other_exit = ExitDTO(other_exit, other_id)
        if content.is_new:
            save_object(other_room)
            area.rooms.append(other_room)
            area.inc_next_room(content.dest_id)
            result.next_room_id = area.next_room_id
            result.new_room = RoomStubDTO(other_room)
            save_object(area, True)
        elif not content.one_way:
            save_object(other_room, True)
        result.exit = ExitDTO(this_exit, room.dbo_id)
        return result

class DeleteExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.start_room, session)
        direction = Direction.ref_map[content.dir]
        local_exit = room.find_exit(direction)
        if not local_exit:
            raise DataError('Exit does not exist')
        contents = save_contents(room)
        room.exits.remove(local_exit)
        save_object(room, True)
        restore_contents(room, contents)

        result = RootDTO()
        result.exit = ExitDTO(local_exit, room.dbo_id)
        if not content.both_sides:
            return result
        other_room = local_exit.destination
        other_exit = other_room.find_exit(direction.rev_dir)
        if not other_exit:
            return result
        other_room.exits.remove(other_exit)
        if not other_room.dbo_rev and not other_room.exits:
            other_room.dbo_rev = -1
            delete_object(other_room)
            area.rooms.remove(other_room)
            result.room_deleted = other_room.dbo_id
            save_object(area)
        else:
            result.other_exit = ExitDTO(other_exit, other_room.dbo_id)
            save_object(other_room)
        return result

def get_room(room_id, session=None):
    area_id = room_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("AREA_MISSING")
    room = area.get_room(room_id)
    if not room:
        raise DataError("ROOM_MISSING")
    if session:
        check_perm(session, area)
    return area, room

def save_contents(start_room):
    safe_room = Room("safe_room", "A Temporary Safe Room")
    contents = []
    for entity in start_room.contents:
        if hasattr(entity, 'change_env'):
            entity.change_env(safe_room)
            contents.append(entity)
    return contents

def restore_contents(room, contents):
    for entity in contents:
        entity.change_env(room)


class RoomStubDTO(RootDTO):
    def __init__(self, room):
        self.id = room.dbo_id
        self.title = room.title
        self.exit_count = len(room.exits)
        self.item_count = len(room.article_resets)
        self.mobile_count = len(room.mobile_resets)
        self.extra_count = len(room.extras)

class ExitDTO(RootDTO):
    def __init__(self, exit, start_id=None):
        self.start_id = start_id
        self.dest_id = exit.destination.dbo_id
        self.dest_title = exit.destination.title
        self.dest_desc = exit.destination.desc
        self.dir = exit.dir_name
        self.two_way = False
        if (exit.destination.find_exit(exit.direction.rev_dir)):
            self.two_way = True

class MobileDTO(RootDTO):
    def __init__(self, mobile_reset):
        self.merge_dict(mobile_reset.json_obj)
        mobile = mud.get_mobile(mobile_reset.mobile_id)
        if mobile:
            self.desc = mobile.desc if mobile.desc else mobile.title
            self.title = mobile.title
        else:
            self.desc = '<MISSING>'
            self.title = '<MISSING>'

class ArticleDTO(RootDTO):
    def __init__(self, article_reset):
        self.merge_dict(article_reset.json_obj)
        article = mud.get_article(article_reset.article_id)
        if article:
            self.desc = article.desc if article.desc else article.title
            self.title = article.title
        else:
            self.desc = '<MISSING>'
            self.title = '<MISSING>'

class RoomDTO(RootDTO):
    def __init__(self, area, room):
        self.id = room.dbo_id
        self.title = room.title
        self.desc = room.desc
        self.dbo_rev = room.dbo_rev
        self.extras = [extra.json_obj for extra in room.extras]
        self.exits = [ExitDTO(exit) for exit in room.exits]
        self.mobiles = [MobileDTO(mobile_reset) for mobile_reset in room.mobile_resets]
        self.articles = [ArticleDTO(article_reset) for article_reset in room.article_resets]



