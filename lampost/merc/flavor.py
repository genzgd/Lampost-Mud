'''
Created on Apr 20, 2012

@author: Geoff
'''
from merc.util import nudge, scale32
from random import randint

class MercFlavor():
    
    def init_mobile(self, mobile):
        mobile.level = nudge(mobile.level)
        mobile.defense = scale32(mobile.level, 100, -100)
        mobile.max_health = mobile.level * 8 + randint(mobile.level * mobile.leve / 4, mobile.level * mobile.level)
        mobile.health = mobile.health
        
    def init_player(self, player):
        player.defense = 100
        player.max_health = 20
        player.health = 20
        player.experience = 0
        
    def apply_player(self, player_cls):
        player_cls.dbo_fields += "level", "defense", "health", "max_health", "status", "experience"
        
    def apply_mobile(self, mobile_cls):
        mobile_cls.dbo_fields += "level",
