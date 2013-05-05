from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'perm', 'mud', __name__)


class MobileResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', MobileList())
        self.putChild('create', MobileCreate())
        self.putChild('delete', MobileDelete())
        self.putChild('get', MobileGet())
        self.putChild('update', MobileUpdate())


class MobileList(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        return [mobile_template.dto_value for mobile_template in area.mobiles]


class MobileGet(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id)
        if not mobile.desc:
            mobile.desc = mobile.title
        return mobile.dto_value


class MobileUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id)
        update_object(mobile, content.model)
        return mobile.dto_value


@requires('cls_registry')
class MobileCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        check_perm(session, area)
        mobile_id = ":".join([area.dbo_id, content.object['id']])
        if area.get_mobile(mobile_id):
            raise DataError(mobile_id + " already exists in this area")
        template = self.cls_registry(MobileTemplate)(mobile_id)
        hydrate_dbo(template, content.object)
        save_object(template)
        area.append_map('mobiles', template)
        save_object(area)
        return template.dto_value


class MobileDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id, session)
        mobile_resets = list(area.find_mobile_resets(mobile.dbo_id))
        if mobile_resets:
            if not content.force:
                raise DataError('InUse:')
            for room, mobile_reset in mobile_resets:
                room.remove_list('mobile_resets', mobile_reset)
                save_object(room, True)
        delete_object(mobile)
        area.remove_map('mobiles', mobile)
        save_object(area)


def get_mobile(mobile_id, session=None):
    area_id = mobile_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("AREA_MISSING")
    mobile = area.get_mobile(mobile_id)
    if not mobile:
        raise DataError("MOBILE_MISSING")
    if session:
        check_perm(session, area)
    return area, mobile
