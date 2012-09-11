from twisted.web.resource import Resource

from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO
from lampost.env.room import Room
from lampost.model.item import BaseItem
from lampost.util.lmutil import DataError

__author__ = 'Geoff'

m_requires('datastore', 'perm', 'mud', __name__)

def get_room(room_id):
    area_id = room_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("Missing Area")
    room = area.get_room(room_id)
    if not room:
        raise DataError("Missing Room")
    return room

def save_contents(start_room):
    safe_room = Room("safe_room")
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

class RoomDTO(RootDTO):
    def __init__(self, room):
        self.basic = RootDTO()
        self.basic.id = room.dbo_id
        self.basic.title = room.title
        self.basic.desc = room.desc
        self.basic.dbo_rev = room.dbo_rev
        self.extras = [extra.json_obj for extra in room.extras]


class RoomResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', RoomList())
        self.putChild('get', RoomGet())
        self.putChild('update_basic', RoomUpdateBasic())
        self.putChild('update_extras', RoomUpdateExtras())

class RoomList(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        if not area:
            raise DataError("Missing Area")
        return [RoomStubDTO(room) for room in area.sorted_rooms]


class RoomGet(Resource):
    @request
    def render_POST(self, content, session):
        return RoomDTO(get_room(content.room_id))


class RoomUpdateBasic(Resource):
    @request
    def render_POST(self, content, session):
        room = get_room(content.id)
        check_perm(session, room)
        contents = save_contents(room)
        room.title = content.title
        room.desc = content.desc
        save_object(room, True)
        restore_contents(room, contents)
        return RoomDTO(room).basic

class RoomUpdateExtras(Resource):
    @request
    def render_POST(self, content, session):
        room = get_room(content.room_id)
        check_perm(session, room)
        contents = save_contents(room)
        room.extras = []
        for extra_json in content.extras:
            if extra_json.get('title', None):
                extra = BaseItem()
                load_json(extra, extra_json)
                room.extras.append(extra)
        save_object(room, True)
        restore_contents(room, contents)
        return RoomDTO(room).extras



