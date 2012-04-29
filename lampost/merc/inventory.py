'''
Created on Apr 29, 2012

@author: Geoff
'''
from lampost.merc.constants import MAX_ITEMS, weight_capacity
from lampost.comm.broadcast import Broadcast

def check_inven(self, article):
    max_items = self.curr_dex * 2 + MAX_ITEMS
    if len(self.inven) >= max_items:
        return Broadcast(s="You cannot juggle any more items!", e="{n} tries to pick up {N}, but can't juggle it.", source=self, target=article)
    item_weight = sum(item.weight for item in self.inven)
    if item_weight + article.weight > weight_capacity(self.curr_str):
        return Broadcast(s="{N} is too heavy for you to lift.", e="{n} tries to pick up {N}, but stumbles under its weight.", source=self, target=article)