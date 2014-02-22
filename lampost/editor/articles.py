from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.areas import parent_area, AreaListResource
from lampost.editor.base import EditResource
from lampost.env.room import Room
from lampost.model.article import ArticleTemplate

m_requires('datastore', 'perm', 'edit_update_service', __name__)


class ArticleResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, ArticleTemplate)
        self.putChild('list', AreaListResource(ArticleTemplate))
        self.putChild('test_delete', ArticleTestDelete())

    def pre_create(self, dto, session):
        check_perm(session, parent_area(dto))

    def pre_update(self, dbo, new_dto, session):
        check_perm(session, parent_area(dbo))

    def pre_delete(self, dbo, session):
        check_perm(session, parent_area(dbo))

    def post_delete(self, article, session):
        for room_id in fetch_set_keys(article.reset_key):
            room = load_object(Room, room_id)
            if room:
                for article_reset in list(room.article_resets):
                    if article_reset.article_id == article.dbo_id:
                        room.article_resets.remove(article_reset)
                save_object(room)
                publish_edit('update', room, session, True)


class ArticleTestDelete(Resource):
    @request
    def render_POST(self, raw):
        article = load_object(ArticleTemplate, raw['dbo_id'])
        if not article:
            raise DataError("GONE:  Article is missing")
        return list(fetch_set_keys(article.reset_key))
