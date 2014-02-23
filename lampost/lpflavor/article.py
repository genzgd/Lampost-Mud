from lampost.comm.broadcast import BroadcastMap
from lampost.datastore.dbo import DBOTField
from lampost.datastore.auto import TemplateField
from lampost.model.article import Article, ArticleTemplate
from lampost.mud.action import mud_action


class ArticleTemplateLP(ArticleTemplate):
    remove_msg = BroadcastMap(s="You unequip {N}", e="{N} unequips {n}")
    equip_msg = BroadcastMap(s="You wear {N}", e="{n} wears {N}")

    def on_loaded(self):
        if self.art_type == 'weapon':
            self.equip_msg = BroadcastMap(s="You wield {N}", e="{n} wields {N}")


class ArticleLP(Article):
    weapon_type = DBOTField('mace')
    damage_type = DBOTField('blunt')
    delivery = DBOTField('melee')
    equip_msg = TemplateField()
    remove_msg = TemplateField()

    def on_equipped(self, equipper):
        equipper.broadcast(target=self, broadcast_map=self.equip_msg)

    def on_removed(self, remover):
        remover.broadcast(target=self, broadcast_map=self.remove_msg)


@mud_action(('wear', 'equip', 'wield'), 'wear')
def wear(source, target, target_method, **_):
    target_method()
    source.equip_article(target)


@mud_action(('remove', 'unequip', 'unwield'), 'remove')
def remove(source, target, target_method, **_):
    target_method()
    source.remove_article(target)
