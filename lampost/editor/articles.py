from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.model.article import ArticleTemplate
from lampost.util.lmutil import DataError

m_requires('datastore', 'perm', 'mud', __name__)

class ArticleResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', ArticleList())
        self.putChild('create', ArticleCreate())
        self.putChild('delete', ArticleDelete())
        self.putChild('get', ArticleGet())
        self.putChild('update', ArticleUpdate())

class ArticleList(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        return [article_template.dto_value for article_template in area.articles]

class ArticleGet(Resource):
    @request
    def render_POST(self, content, session):
        area, article = get_article(content.object_id)
        if not article.desc:
            article.desc = article.title
        return article.dto_value

class ArticleUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, article = get_article(content.object_id, session)
        update_object(article, content.model)
        return article.dto_value

@requires('cls_registry')
class ArticleCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        check_perm(session, area)
        article_id = ":".join([area.dbo_id, content.object.id])
        if area.get_article(article_id):
            raise DataError(article_id + " already exists in this area")
        template = self.cls_registry(ArticleTemplate)(article_id)
        load_json(template, content.object)
        save_object(template)
        area.articles.append(template)
        save_object(area)
        return template.dto_value

class ArticleDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, article = get_article(content.object_id, session)
        article_resets = list(area.find_article_resets(article.dbo_id))
        if article_resets:
            if not content.force:
                raise DataError('IN_USE')
            for room, article_reset in article_resets:
                room.article_resets.remove(article_reset)
                save_object(room, True)
        delete_object(article)
        area.articles.remove(article)
        save_object(area)


def get_article(article_id, session=None):
    area_id = article_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("AREA_MISSING")
    article = area.get_article(article_id)
    if not article:
        raise DataError("OBJECT_MISSING")
    if session:
        check_perm(session, area)
    return area, article
