from lampost.datastore.dbo import DBOField
from lampost.model.article import Article
from lampost.mud.action import mud_action


class ArticleLP(Article):

    weapon_type = DBOField('mace')
    damage_type = DBOField('blunt')
    delivery = DBOField('melee')


@mud_action(('wear', 'equip', 'wield'), 'wear')
def wear(source, target, target_method, **ignored):
    target_method()
    source.equip_article(target)


@mud_action(('remove', 'unequip', 'unwield'), 'remove')
def remove(source, target, target_method, **ignored):
    target_method()
    source.remove_article(target)
