from lampost.model.article import Article


class ArticleLP(Article):
    template_fields = "weapon_type", "damage_type", "delivery"
    weapon_type = 'mace'
    damage_type = 'blunt'
    delivery = 'melee'
