'''
Created on Apr 20, 2012

@author: Geoff
'''
from lampost.merc.util import nudge, scale32
from lampost.merc.combat import mob_rec_violence, player_calc_damage, mob_calc_damage,  mob_rec_damage,\
    player_rec_violence, mob_attack, player_rec_damage, player_auto_attack
from lampost.merc.player import soul, curr_str, curr_dex
from random import randint
from lampost.mobile.mobile import Mobile
from lampost.model.article import Article
from lampost.merc.inventory import check_inven

class MercFlavor():
    flavor = "merc2.2"

    def init_mobile(self, mobile):
        mobile.level = nudge(mobile.level if mobile.level else 1)
        mobile.defense = scale32(mobile.level, 100, -100)
        mobile.max_health = mobile.level * 8 + randint(mobile.level * mobile.level / 4, mobile.level * mobile.level)
        mobile.health = mobile.max_health

    def init_player(self, player):
        player.defense = 100
        player.max_health = 20
        player.health = 20
        player.experience = 0
        player.level = 1
        player.perm_str = player.perm_wis = player.perm_int = player.perm_con = player.perm_dex = 13

    def enhance_player(self, player):
        player.enhance_soul(soul)
        player.mod_str = player.mod_wis = player.mod_int = player.mod_con = player.mod_dex = 0
        player.item_weight = 0

    def apply_player(self, player_cls):
        player_cls.dbo_fields += "level", "defense", "health", "max_health", "status", "experience", \
            "perm_str", "perm_dex", "perm_wis", "perm_int", "perm_con"
        player_cls.rec_violence = player_rec_violence
        player_cls.calc_damage = player_calc_damage
        player_cls.rec_damage = player_rec_damage
        player_cls.auto_attack = player_auto_attack
        player_cls.curr_str = property(curr_str)
        player_cls.curr_dex = property(curr_dex)
        player_cls.check_inven = check_inven

    def apply_mobile(self, mobile_cls):
        mobile_cls.dbo_fields += "level",
        mobile_cls.rec_violence = mob_rec_violence
        mobile_cls.calc_damage = mob_calc_damage
        mobile_cls.rec_damage = mob_rec_damage
        mobile_cls.mob_attack = mob_attack

    def apply_mobile_template(self, mobile_template_cls):
        mobile_template_cls.template_fields = Mobile.dbo_fields
        mobile_template_cls.dbo_fields = Mobile.dbo_fields + ("dbo_rev", "instance_class", "world_max")
        mobile_template_cls.level = 1

    def apply_article(self, article_cls):
        article_cls.dbo_fields += "level",

    def apply_article_template(self, article_template_cls):
        article_template_cls.template_fields = Article.dbo_fields
        article_template_cls.dbo_fields = Article.dbo_fields + ("dbo_rev", "instance_class", "world_max")
        article_template_cls.weight = 1
        article_template_cls.level = 1


