from random import randint
from lampost.comm.broadcast import Broadcast
from lampost.merc.combat import basic_hit
from lampost.merc.constants import MAX_ITEMS, weight_capacity
from lampost.player.player import Player

class PlayerMerc(Player):

    dbo_fields = Player.dbo_fields + ("level", "defense", "health", "max_health", "status", "experience",
                 "perm_str", "perm_dex", "perm_wis", "perm_int", "perm_con")
    defense = 100
    max_health = 20
    health = 20
    experience = 0
    level = 1
    perm_str = perm_wis = perm_int = perm_con = perm_dex = 13
    mod_str = mod_wis = mod_int = mod_con = mod_dex = 0

    def rec_damage(self, damage):
        pass

    def calc_damage(self, target):
        damage = randint(1, 4)
        return damage

    def rec_violence(self, opponent):
        if not self.current_target:
            self.combat_pulse = self.register_p(self.auto_attack, seconds=3)
            self.current_target = opponent

    def auto_attack(self):
        if self.current_target:
            if self.current_target.env == self.env:
                self.env.rec_broadcast(basic_hit(self, self.current_target))
            else:
                self.current_target = None
                self.unregister(self.combat_pulse)

    def check_inven(self, article):
        max_items = self.curr_dex * 2 + MAX_ITEMS
        if len(self.inven) >= max_items:
            return Broadcast(s="You cannot juggle any more items!", e="{n} tries to pick up {N}, but can't juggle it.", source=self, target=article)
        item_weight = sum(item.weight for item in self.inven)
        if item_weight + article.weight > weight_capacity(self.curr_str):
            return Broadcast(s="{N} is too heavy for you to lift.", e="{n} tries to pick up {N}, but stumbles under its weight.", source=self, target=article)

    @property
    def curr_dex(self):
        return max(3, self.perm_dex + self.mod_dex)

    @property
    def curr_str(self):
        return max(3, self.perm_str + self.mod_str)