from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.editor.base import EditListResource, EditResource, EditCreateResource, EditDeleteResource, EditUpdateResource
from lampost.lpflavor.combat import AttackSkill, DefenseSkill

m_requires('skill_service', __name__)


class AttackResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, AttackSkill)

    def on_delete(self, del_obj, session):
        skill_service.skills.pop(del_obj.dbo_id, None)

    def on_create(self, new_obj, session):
        skill_service.skills[new_obj.dbo_id] = new_obj


class DefenseResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, DefenseSkill)

    def on_delete(self, del_obj, session):
        skill_service.skills.pop(del_obj.dbo_id, None)

    def on_create(self, new_obj, session):
        skill_service.skills[new_obj.dbo_id] = new_obj


class AllSkillsResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('all', AllList())


class AllList(Resource):
    @request
    def render_POST(self):
        return {dbo_id: skill.desc for dbo_id, skill in skill_service.skills.iteritems()}




