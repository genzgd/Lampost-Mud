from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.dto.rootdto import RootDTO
from lampost.mud.area import Area

__author__ = 'Geoff'

m_requires('datastore', 'mud', 'perm', __name__)

class AreaDTO(RootDTO):
    def __init__(self, area, can_write):
        self.id = area.dbo_id
        self.dbo_rev = area.dbo_rev
        self.name = area.name
        self.owner_id = area.owner_id
        self.rooms = len(area.rooms)
        self.items = len(area.articles)
        self.mobiles = len(area.mobiles)
        self.next_room_id = area.next_room_id
        self.can_write = can_write

class AreaResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', AreaList())
        self.putChild('new', AreaNew())
        self.putChild('delete', AreaDelete())
        self.putChild('update', AreaUpdate())

class AreaList(Resource):
    @request
    def render_POST(self, content, session):
        return [AreaDTO(area, has_perm(session.player, area)) for area in mud.area_map.itervalues()]

@requires('mud')
class AreaNew(Resource):
    @request
    def render_POST(self, content, session):
        area_id = content.id.lower()
        if datastore.load_object(Area, area_id):
                return "AREA_EXISTS"
        area = Area(area_id)
        area.name = content.name
        area.owner_id = session.player.dbo_id
        datastore.save_object(area)
        self.mud.add_area(area)
        return AreaDTO(area)


@requires('mud', 'dispatcher')
class AreaDelete(Resource):
    @request
    def render_POST(self, content, session):
        area_id = content.areaId.lower()
        area = datastore.load_object(Area, area_id)
        if area:
            check_perm(session, area)
            self.dispatcher.detach_events(area)
            datastore.delete_object(area)
            del self.mud.area_map[area_id]
            return "OK"


class AreaUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area_dto = content.area
        area = datastore.load_object(Area, area_dto['id'])
        if not area:
            return "ERROR_NOT_FOUND"
        check_perm(session, area)
        area.name = area_dto['name']
        area.next_room_id = area_dto['next_room_id']
        datastore.save_object(area, True)
        return AreaDTO(area)



