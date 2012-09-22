from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO
from lampost.mobile.mobile import MobileTemplate
from lampost.util.lmutil import DataError

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
        return [MobileDTO(mobile_template) for mobile_template in area.mobiles]

class MobileGet(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id)
        if not mobile.desc:
            mobile.desc = mobile.title
        return MobileDTO(mobile)

class MobileUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id)
        update_object(mobile, content.model)
        return MobileDTO(mobile)

class MobileCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        mobile = RootDTO().merge_dict(content.object)
        check_perm(session, area)
        mobile_id = ":".join([area.dbo_id, mobile.id])
        if area.get_mobile(mobile_id):
            raise DataError(mobile_id + " already exists in this area")
        template = MobileTemplate(mobile_id, mobile.title)
        template.desc = mobile.desc
        template.level = mobile.level
        save_object(template)
        area.mobiles.append(template)
        save_object(area)
        return MobileDTO(template)

class MobileDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, mobile = get_mobile(content.object_id, session)
        mobile_resets = list(area.find_mobile_resets(mobile.dbo_id))
        if mobile_resets:
            if not content.force:
                raise DataError('IN_USE')
            for room, mobile_reset in mobile_resets:
                room.mobile_resets.remove(mobile_reset)
                save_object(room, True)
        delete_object(mobile)
        area.mobiles.remove(mobile)
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

class MobileDTO(RootDTO):
    def __init__(self, mobile_template):
        self.merge_dict(mobile_template.json_obj)
        self.dbo_id = mobile_template.dbo_id