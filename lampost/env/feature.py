from lampost.datastore.classes import get_dbo_class
from lampost.context.resource import m_requires
from lampost.model.item import BaseItem

m_requires('log', __name__)


class Feature(BaseItem):
    class_id = 'feature'

    @classmethod
    def load_ref(cls, dbo_repr, owner=None):
        try:
            feature_cls = get_dbo_class(dbo_repr['sub_class_id'])
        except KeyError:
            error("Feature missing subclass id {} in room {}".format(dbo_repr, owner.dbo_id))
            return
        feature = feature_cls()
        feature.room = owner
        feature.hydrate(dbo_repr)
        try:
            feature.on_created()
        except AttributeError:
            pass
        return feature
