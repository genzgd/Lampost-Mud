from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.mud.socials import Social
from lampost.util.lmutil import StateError

m_requires('datastore', 'perm', 'mud', __name__)

class SocialsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', SocialList())
        self.putChild('get', SocialGet())
        self.putChild('delete', SocialDelete())
        self.putChild('update', SocialUpdate())
        self.putChild('valid', SocialValid())

class SocialList(Resource):
    @request
    def render_POST(self, content, session):
        check_perm(session, 'admin')
        return list(fetch_set_keys('socials'))

class SocialGet(Resource):
    @request
    def render_POST(self, content, session):
        return load_object(content.social_id)

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

@requires('social_registry', 'mud_actions')
class SocialValid(Resource):
    @request
    def render_POST(self, content, session):
        if self.social_registry.get(content.social_id):
            raise StateError("Social already exists")
        if self.mud_actions.verbs.get(content.social_id):
            raise StateError("Verb already in use")


