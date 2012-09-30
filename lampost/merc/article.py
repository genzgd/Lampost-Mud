from lampost.model.article import ArticleTemplate

class ArticleTemplateMerc(ArticleTemplate):
    new_fields = ("level",)
    template_fields = ArticleTemplate.template_fields + new_fields
    dbo_fields = ArticleTemplate.dbo_fields + new_fields
    level = 1