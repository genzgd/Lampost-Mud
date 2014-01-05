from lampost.comm.broadcast import BroadcastMap
from lampost.datastore.dbo import DBOField, ProtoField
from lampost.model.article import Article, ArticleTemplate
from lampost.mud.action import mud_action


class ArticleTemplateLP(ArticleTemplate):
    remove_msg = BroadcastMap(s="You unequip {N}", e="{N} unequips {n}")
    equip_msg = BroadcastMap(s="You wear {N}", e="{n} wears {N}")

    def on_loaded(self):
        if self.art_type == 'weapon':
            self.equip_msg = BroadcastMap(s="You wield {N}", e="{n} wields {N}")
        super(ArticleTemplateLP, self).on_loaded()


class ArticleLP(Article):
    weapon_type = DBOField('mace')
    damage_type = DBOField('blunt')
    delivery = DBOField('melee')
    equip_msg = ProtoField()
    remove_msg = ProtoField()

    def on_equipped(self, equipper):
        equipper.broadcast(target=self, broadcast_map=self.equip_msg)

    def on_removed(self, remover):
        remover.broadcast(target=self, broadcast_map=self.remove_msg)


@mud_action(('wear', 'equip', 'wield'), 'wear')
def wear(source, verb, target, target_method, **ignored):
    target_method()
    source.equip_article(target)


@mud_action(('remove', 'unequip', 'unwield'), 'remove')
def remove(source, verb, target, target_method, **ignored):
    target_method()
    source.remove_article(target)
