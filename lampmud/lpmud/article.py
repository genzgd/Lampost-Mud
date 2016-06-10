from lampmud.comm.broadcast import BroadcastMap
from lampost.meta.auto import TemplateField
from lampost.db.dbofield import DBOField, DBOTField
from lampmud.model.article import Article, ArticleTemplate
from lampmud.mud.action import mud_action


class ArticleTemplateLP(ArticleTemplate):
    class_id = 'article'

    remove_msg = BroadcastMap(s="You unequip {N}", e="{n} unequips {N}")
    equip_msg = BroadcastMap(s="You wear {N}", e="{n} wears {N}")
    wield_msg = BroadcastMap(s="You wield {N}", e="{n} wields {N}")

    def _on_loaded(self):
        if self.art_type == 'weapon':
            self.equip_msg = self.wield_msg


class ArticleLP(Article):
    equip_slot = DBOTField()
    current_slot = DBOField()

    weapon_type = DBOTField('mace')
    damage_type = DBOTField('blunt')
    delivery = DBOTField('melee')
    equip_msg = TemplateField()
    remove_msg = TemplateField()

    def on_equipped(self, equipper):
        equipper.broadcast(target=self, broadcast_map=self.equip_msg)

    def on_removed(self, remover):
        remover.broadcast(target=self, broadcast_map=self.remove_msg)


@mud_action(('wear', 'equip', 'wield'), 'equip_slot', target_class="inven")
def wear(source, target, **_):
    source.equip_article(target)


@mud_action(('remove', 'unequip', 'unwield'), 'current_slot')
def remove(source, target,  **_):
    source.remove_article(target)
