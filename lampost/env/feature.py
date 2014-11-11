from lampost.datastore.classes import get_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField
from lampost.gameops.script import Scriptable
from lampost.model.item import BaseItem

m_requires('log', __name__)


class Feature(BaseItem, Scriptable):
    class_id = 'feature'

    editor = DBOField(False)
    edit_required = DBOField(False)

    @classmethod
    def load_ref(cls, dbo_repr, owner=None):
        try:
            feature_cls = dbo_repr['sub_class_id']
        except KeyError:
            error("Feature missing subclass id {} in room {}".format(dbo_repr, owner.dbo_id))
            return
        feature = get_dbo_class(feature_cls)()
        feature.room = owner
        feature.hydrate(dbo_repr)
        if hasattr(feature, 'on_created'):
            feature.on_created()
        return feature

