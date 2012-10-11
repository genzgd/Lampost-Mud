from random import randint
from lampost.action.action import ActionError
from lampost.merc.combat import basic_hit
from lampost.merc.constants import MAX_ITEMS, weight_capacity, MAX_LEVEL, XP_PER_LEVEL
from lampost.player.player import Player

class PlayerMerc(Player):

    dbo_fields = Player.dbo_fields + ("level", "health", "max_health", "status", "experience",
                 "perm_str", "perm_dex", "perm_wis", "perm_int", "perm_con")
    defense = 100
    max_health = 20
    health = 20
    experience = 0
    level = 1
    perm_str = perm_wis = perm_int = perm_con = perm_dex = 13
    mod_str = mod_wis = mod_int = mod_con = mod_dex = 0
    weapon = None

    def __init__(self, dbo_id):
        super(PlayerMerc, self).__init__(dbo_id)

    def rec_damage(self, damage):
        pass

    def calc_damage(self, target):
        if self.weapon:
            damage = randint(self.weapon.damage_low, self.weapon.damage_high)
        else:
            damage = randint(1, 4)
        return damage

    def rec_violence(self, opponent):
        if not self.current_target:
            self.combat_pulse = self.register_p(self.auto_attack, seconds=3)
            self.current_target = opponent

    def auto_attack(self):
        if self.current_target:
            if self.current_target.env == self.env:
                basic_hit(self, self.current_target)
            else:
                self.current_target = None
                self.unregister(self.combat_pulse)

    def equip_article(self, article):
        if not article in self.inven:
            raise ActionError('You must pick up the item before you can equip it.')
        if article.slot == 'none':
            raise ActionError('This is not something you can equip.')
        if self.level < article.level:
            raise ActionError('That item is too powerful for you.')

        if article.type == 'weapon' and self.weapon:
            self.remove_article(self.weapon)
        equip_slot = self._equip_slot(article.slot)
        if self._slot_filled(equip_slot):
            self._remove_by_slot(equip_slot)
            if self._slot_filled(equip_slot):
                raise ActionError('You have no place to put that.')
        self._do_equip(article, equip_slot)
        if article.type == 'weapon':
            self.weapon = article

    def remove_article(self, article):
        if not article.equip_slot:
            raise ActionError("{0} is not equipped.".format(article.name))
        if not article in self.inven:
            raise ActionError("{0} is not yours.".format(article.name))
        if article.equip_slot == 'two_hand':
            self.equip_slots['r_hand'] = None
            self.equip_slots['l_hand'] = None
        else:
            self.equip_slots[article.equip_slot] = None
        article.equip_slot = None
        if article.type == 'weapon':
            self.weapon = None
        self._unadjust_stats(article)
        self.broadcast(s="You remove {N}", e="{n} removes {N}", target=article)

    def check_inven(self, article):
        max_items = self.curr_dex * 2 + MAX_ITEMS
        if len(self.inven) >= max_items:
            self.broadcast(s="You cannot juggle any more items!", e="{n} tries to pick up {N}, but can't juggle it.", target=article)
        item_weight = sum(item.weight for item in self.inven)
        if item_weight + article.weight > weight_capacity(self.curr_str):
            self.broadcast(s="{N} is too heavy for you to lift.", e="{n} tries to pick up {N}, but stumbles under its weight.", target=article)

    def _do_equip(self, article, equip_slot):
        self.equip_slots[equip_slot] = article
        article.equip_slot = equip_slot
        self._adjust_stats(article)
        self.broadcast(s="You wear {N}", e="{n} wears {N}",  target=article)

    def _adjust_stats(self, article):
        self.defense -= getattr(article, 'defense', 0)

    def _unadjust_stats(self, article):
        self.defense += getattr(article, 'defense', 0)

    def _remove_by_slot(self, equip_slot):
        if equip_slot == 'two_hand':
            self._remove_by_slot('r_hand')
            self._remove_by_slot('l_hand')
            return
        article = self.equip_slots.get(equip_slot)
        if article:
            self.remove_article(article)

    def _equip_slot(self, equip_slot):
        if equip_slot == 'finger':
            if self._slot_filled('r_finger'):
                return 'r_finger'
            return 'l_finger'
        elif equip_slot == 'wrist':
            if self._slot_filled('r_wrist'):
                return 'r_wrist'
            return 'l_wrist'
        elif equip_slot == 'one-hand':
            if self._equip_slot('r_hand'):
                return 'r_hand'
            return 'l_hand'
        return equip_slot

    def _slot_filled(self, equip_slot):
        if equip_slot == 'two-hand':
            if self.equip_slots.get('r_hand') or self.equip_slots.get('l_hand'):
                return None
        return self.equip_slots.get(equip_slot)

    def get_score(self):
        score = super(PlayerMerc, self).get_score()
        score.level = self.level
        score.defense = self.defense
        score.experience = self.experience
        return score

    def add_exp(self, exp):
        self.experience += exp
        while self.level < MAX_LEVEL and self.experience < (self.level - 1) * XP_PER_LEVEL:
            self.add_level()

    def add_level(self):
        self.level += 1
        new_hp = randint(11, 15)
        self.max_health += new_hp
        self.health += new_hp
        self.display_line("You have achieved level {0}!".format(self.level))

    @property
    def curr_dex(self):
        return max(3, self.perm_dex + self.mod_dex)

    @property
    def curr_str(self):
        return max(3, self.perm_str + self.mod_str)