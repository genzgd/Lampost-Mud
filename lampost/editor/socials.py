from twisted.web.resource import Resource

from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.mud.socials import Social
from lampost.util.lmutil import DataError, Blank
from lampost.comm.broadcast import BroadcastMap, Broadcast, broadcast_types

m_requires('datastore', 'perm', 'mud', __name__)

class SocialsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', SocialList())
        self.putChild('get', SocialGet())
        self.putChild('delete', SocialDelete())
        self.putChild('update', SocialUpdate())
        self.putChild('valid', SocialValid())
        self.putChild('preview', SocialPreview())
        self.putChild('copy', SocialCopy())

class SocialList(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        return list(fetch_set_keys('socials'))

class SocialGet(Resource):
    @request
    def render_POST(self, content, session):
        return load_object(Social, content.social_id)

@requires('cls_registry', 'social_registry')
class SocialUpdate(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        social = self.cls_registry(Social)(content.social_id.lower())
        social.map = content.map
        save_object(social)
        self.social_registry.insert(social)

@requires('social_registry')
class SocialDelete(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        social = Social(content.social_id)
        delete_object(social)
        self.social_registry.delete(content.social_id)

@requires('mud_actions')
class SocialValid(Resource):
    @request
    def render_POST(self, content, session):
        if self.mud_actions.verb_list((content.social_id,)):
            raise DataError("Verb already in use")

class SocialPreview(Resource):
    @request
    def render_POST(self, content, session):
        preview = {}
        source = Blank()
        source.name = content.source
        if content.self_source:
            target = source
        else:
            target = Blank()
            target.name = content.target
        broadcast_map = BroadcastMap()
        broadcast_map.populate(content.map)
        broadcast = Broadcast(broadcast_map, source, target)
        for broadcast_type in broadcast_types:
            preview[broadcast_type['id']] = broadcast.substitute(broadcast_type['id'])
        return preview

@requires('social_registry', 'mud_actions')
class SocialCopy(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        if self.mud_actions.verb_list((content.copy_id,)):
            raise StateError("Verb already in use")
        copy = load_object(Social, content.original_id)
        copy.dbo_id = content.copy_id
        save_object(copy)
        self.social_registry.insert(copy)
        return copy



