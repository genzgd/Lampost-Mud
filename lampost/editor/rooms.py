from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import requires, m_requires
from lampost.dto.rootdto import RootDTO

__author__ = 'Geoff'

m_requires('datastore', __name__)

class RoomDTO(RootDTO):
    def __init__(self, room):
        self.id = room.dbo_id
        self.title = room.title
        self.exit_count = len(room.exits)
        self.item_count = len(room.article_resets)
        self.mobile_count = len(room.mobile_resets)
        self.extra_count = len(room.extras)

class RoomResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', RoomList())

@requires('mud')
class RoomList(Resource):
    @request
    def render_POST(self, content, session):
        area = self.mud.get_area(content.area_id)
        if not area:
            return "ERROR_NO_AREA"
        return [RoomDTO(room) for room in area.sorted_rooms]

