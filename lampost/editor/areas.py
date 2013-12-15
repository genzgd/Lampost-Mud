from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.model.area import Area

m_requires('datastore', 'mud', 'perm', 'dispatcher', __name__)


class AreaResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Area)

    def on_create(self, new_area):
        mud.add_area(new_area)

    def on_delete(self, del_area):
        for room in del_area.rooms.itervalues():
            delete_room(room, del_area.dbo_id)
        del mud.area_map[del_area.dbo_id]


class AreaListResource(Resource):
    def __init__(self, list_class):
        Resource.__init__(self)
        self.list_class = list_class

    def getChild(self, area_id, request):
        return self.list_class(area_id)


class RoomResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Room)
        self.putChild('list', AreaListResource(RoomListResource))

    def pre_create(self, room_dto, session):
        area = room_area(room_dto)
        check_perm(session, area)

    def on_create(self, room):
        area = room_area(room)
        area.add_coll_item('rooms', room)
        area.inc_next_room(room)
        dispatch('edit_update', 'update', area.dto_value)

    def pre_delete(self, room, session):
        check_perm(session, room_area(room))

    def on_delete(self, room):
        save_contents(room)
        delete_room(room)
        room_area(room).del_coll_item('rooms', room)


class RoomListResource(Resource):
    def __init__(self, area_id):
        Resource.__init__(self)
        self.area_id = area_id
        self.imm_level = 'admin'

    @request
    def render_POST(self):
        return [load_object(Room, room_id).dto_value for room_id in fetch_set_keys('area_rooms:{}'.format(self.area_id))]


def room_area(room):
    try:
        dbo_id = room.dbo_id
    except AttributeError:
        dbo_id = room['dbo_id']
    area = load_object(Area, dbo_id.split(':')[0])
    if not area:
        raise DataError("Area Missing")
    return area


def delete_room(room, area_delete=None):
    for my_exit in room.exits:
        other_room = my_exit.destination
        if other_room.area_id == area_delete:
            continue
        for other_exit in other_room.exits:
            if other_exit.destination == room:
                other_contents = save_contents(other_room)
                other_room.exits.remove(other_exit)
                save_object(other_room, True)
                restore_contents(other_room, other_contents)


def save_contents(start_room):
    safe_room = Room("safe_room", "A Temporary Safe Room")
    contents = []
    for entity in start_room.contents[:]:
        if hasattr(entity, 'change_env'):
            entity.change_env(safe_room)
            contents.append(entity)
    return contents
