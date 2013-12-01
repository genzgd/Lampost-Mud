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
        self.putChild('dir_list', DirList())


class DirList(Resource):
    @request
    def render_POST(self):
        return [{'key':direction.key, 'name':direction.desc} for direction in Direction.ordered]


class RoomListResource(Resource):
    def __init__(self, area_id):
        Resource.__init__(self)
        self.area_id = area_id
        self.imm_level = 'admin'

    @request
    def render_POST(self):
        area = mud.get_area(self.area_id)
        if not area:
            raise DataError("Missing Area")
        return [room.dto_value for room in area.rooms.values()]


def room_stub_dto(room):
    return {'dbo_id': room.dbo_id, 'title': room.title, 'exit_count': len(room.exits), 'item_count': len(room.article_resets),
            'mobile_count': len(room.mobile_resets), 'extra_count': len(room.extras)}



