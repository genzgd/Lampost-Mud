from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.areas import AreaListResource, parent_area
from lampost.editor.base import EditResource
from lampost.env.room import Room
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'edit_update_service', 'perm', __name__)


class MobileResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, MobileTemplate)
        self.putChild('list', AreaListResource(MobileTemplate))
        self.putChild('test_delete', MobileTestDelete())

    def pre_create(self, dto, session):
        check_perm(session, parent_area(dto))

    def pre_update(self, dbo, session):
        check_perm(session, parent_area(dbo))

    def pre_delete(self, dbo, session):
        check_perm(session, parent_area(dbo))

    def post_delete(self, mobile, session):
        for room_id in fetch_set_keys(mobile.reset_key):
            room = load_object(Room, room_id)
            if room:
                for mobile_reset in list(room.mobile_resets):
                    if mobile_reset.mobile_id == mobile.dbo_id:
                        room.mobile_resets.remove(mobile_reset)
                save_object(room)
                publish_edit('update', room, session, True)


class MobileTestDelete(Resource):
    @request
    def render_POST(self, raw):
        mobile = load_object(MobileTemplate, raw['dbo_id'])
        if not mobile:
            raise DataError("GONE:  Mobile is missing")
        return list(fetch_set_keys(mobile.reset_key))
