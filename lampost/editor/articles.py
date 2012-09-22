from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.dto.rootdto import RootDTO
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
        return [ArticleDTO(article_template) for article_template in area.articles]

class ArticleGet(Resource):
    @request
    def render_POST(self, content, session):
        area, article = get_article(content.object_id)
        if not article.desc:
            article.desc = article.title
        return ArticleDTO(article)

class ArticleUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, article = get_article(content.object_id, session)
        update_object(article, content.model)
        return ArticleDTO(article)

class ArticleCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        check_perm(session, area)
        article_id = ":".join([area.dbo_id, content.object['id']])
        if area.get_article(article_id):
            raise DataError(article_id + " already exists in this area")
        template = ArticleTemplate(article_id)
        load_json(template, content.object)
        save_object(template)
        area.articles.append(template)
        save_object(area)
        return ArticleDTO(template)

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

class ArticleDTO(RootDTO):
    def __init__(self, article_template):
        self.merge_dict(article_template.json_obj)
        self.dbo_id = article_template.dbo_id