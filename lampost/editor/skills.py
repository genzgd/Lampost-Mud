from lampost.context.resource import m_requires
from lampost.editor.base import EditListResource, EditResource, EditCreateResource, EditDeleteResource, EditUpdateResource
from lampost.lpflavor.combat import AttackSkill

m_requires('skill_service', __name__)


class AttackResource(EditResource):

    def __init__(self):
        EditResource.__init__(self, AttackSkill, 'admin')

    def on_delete(self, del_obj):
        skill_service.skills.pop(del_obj.dbo_id, None)

    def on_add(self, new_obj):
        skill_service.skills[new_obj.dbo_id] = new_obj

