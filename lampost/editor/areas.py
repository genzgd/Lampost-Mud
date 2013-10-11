from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.model.area import Area

m_requires('datastore', 'mud', 'perm', 'dispatcher',__name__)


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
        return [area_dto(area, has_perm(session.player, area)) for area in mud.area_map.itervalues()]


@requires('mud', 'cls_registry')
class AreaNew(Resource):
    @request
    def render_POST(self, content, session):
        area_id = content.id.lower()
        area = self.cls_registry(Area)(area_id)
        area.name = content.name
        area.owner_id = session.player.dbo_id
        create_object(area)
        self.mud.add_area(area)
        return area_dto(area)


@requires('mud')
class AreaDelete(Resource):
    @request
    def render_POST(self, content, session):
        area_id = content.areaId.lower()
        area = datastore.load_object(Area, area_id)
        if area:
            check_perm(session, area)
            detach_events(area)
            delete_object(area)
            del self.mud.area_map[area_id]
            return "OK"


class AreaUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area_info = content.area
        area = datastore.load_object(Area, area_info['id'])
        if not area:
            return "ERROR_NOT_FOUND"
        check_perm(session, area)
        area.name = area_info['name']
        area.next_room_id = area_info['next_room_id']
        save_object(area, True)
        return area_dto(area)


def area_dto(area, can_write=True):
    return {'id': area.dbo_id, 'dbo_rev': area.dbo_rev, 'name': area.name, 'owner_id': area.owner_id, 'room': len(area.rooms),
            'article':len(area.articles), 'mobile': len(area.mobiles), 'next_room_id': area.next_room_id, 'can_write': can_write}




