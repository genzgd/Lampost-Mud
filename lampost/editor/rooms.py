from twisted.web.resource import Resource

from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO
from lampost.env.movement import Direction
from lampost.env.room import Room
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

class DirList(Resource):
    @request
    def render_Post(self, content, session):
        return [{'key':dir.key, 'name':dir.name} for dir in Direction.ref_map.itervalues()]


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
        return RoomDTO(get_room(session, content.room_id)[1])

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
        if area.next_room_id == room_dto['id']:
            next_room_id = content.area_id + ':' + str(area.next_room_id)
            while area.get_room(next_room_id):
                area.next_room_id += 1
                next_room_id = content.area_id + ':' + str(area.next_room_id)
        save_object(area)
        return RootDTO(next_room_id=area.next_room_id, room=RoomStubDTO(room))

class RoomDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(session, content.room_id)
        main_contents = save_contents(room)
        for my_exit in room.exits:
            other_room = my_exit.destination
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_contents = save_contents(other_room)
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    restore_contents(other_room, other_contents)
        delete_object(room)
        area.rooms.remove(room)
        save_object(area, True)
        for entity in main_contents:
            if entity.dbo_key_type == 'player':
                mud.start_player(entity)
            else:
                entity.detach()

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
        area, room = get_room(session, content.id)
        contents = save_contents(room)
        room.title = content.title
        room.desc = content.desc
        room.extras = []
        for extra_json in content.extras:
            if extra_json.get('title', None):
                extra = BaseItem()
                load_json(extra, extra_json)
                room.extras.append(extra)
        save_object(room, True)
        restore_contents(room, contents)
        return RoomDTO(room)

def get_room(session, room_id):
    area_id = room_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("AREA_MISSING")
    room = area.get_room(room_id)
    if not room:
        raise DataError("ROOM_MISSING")
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
    def __init__(self, exit):
        self.dest_id = exit.destination.dbo_id
        self.dest_title = exit.destination.title
        self.dir = exit.dir_name
        self.two_way = False
        if (exit.destination.find_exit(exit.direction.rev_dir)):
            self.two_way = True

class RoomDTO(RootDTO):
    def __init__(self, room):
        self.id = room.dbo_id
        self.title = room.title
        self.desc = room.desc
        self.dbo_rev = room.dbo_rev
        self.extras = [extra.json_obj for extra in room.extras]
        self.exits = [ExitDTO(exit) for exit in room.exits]



