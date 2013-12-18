from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.editor.areas import AreaListResource
from lampost.editor.base import EditResource
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'perm', 'mud', __name__)


class MobileResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, MobileTemplate)
        self.putChild('list', AreaListResource(MobileTemplate))
        self.putChild('test_delete', MobileTestDelete)


class MobileTestDelete(Resource):
    @request
    def render_POST(self, raw, session):
        area, mobile = get_mobile(raw['dbo_id'], session)
        mobile_resets = list(area.find_mobile_resets(mobile.dbo_id))
        if mobile_resets:
            if not content.force:
                raise DataError('InUse:')
            for room, mobile_reset in mobile_resets:
                room.remove_list('mobile_resets', mobile_reset)
                save_object(room, True)
        delete_object(mobile)

