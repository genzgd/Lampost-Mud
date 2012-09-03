from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO

__author__ = 'Geoff'

m_requires('datastore', 'mud',__name__)

class AreaResource(Resource):

    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', AreaList())

class AreaList(Resource):
    @request
    def render_POST(self, content, session):
        list = []
        for key, area in mud.area_map.iteritems():
            dto = RootDTO()
            dto.id = key
            dto.name = area.name
            dto.owner = area.owner_id
            dto.rooms = len(area.rooms)
            dto.items = len(area.articles)
            dto.mobiles = len(area.mobiles)
            dto.next_room = area.next_room_id
            list.append(dto)
        return list



