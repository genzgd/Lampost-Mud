'''
Created on Apr 15, 2012

@author: Geoff
'''
from lampost.action.action import Action
from lampost.comm.broadcast import Broadcast
from lampost.gameops.event import PULSES_PER_SECOND
from lampost.merc.util import scale32
from random import randint


base_thdef0 = 18  # Roll required to hit Defense 0 at level 1
base_thdef32 = 6  # Roll required to hit Defense 0 at level 32

def basic_hit(source, target):
    thdef0 = scale32(source.level, base_thdef0, base_thdef32)  # TODO -- strength modifier
    defense = max(-15, target.defense / 10)
    to_hit_roll = thdef0 - defense
    dice_roll = randint(0, 19)
    if dice_roll == 19 or dice_roll >= to_hit_roll:
        damage = source.calc_damage(target)
        target.rec_damage(damage)
        return Broadcast(None, source, target, s="You hit {N} for " + unicode(damage) + ".", e="{n} hits {N}", t="{n} hits you!");
    else:
        target.rec_damage(0)
        return Broadcast(None, source, target, s="You miss {N}.", e="{n} misses {N}", t="{n} misses you!")        

         
def mob_calc_damage(self, target):
    damage = randint(self.level / 2, self.level * 3 / 2 )
    return damage
    
def player_calc_damage(self, target):
    damage = randint(1, 4);
    return damage
    
def mob_attack(self):
    if self.current_target.env == self.env:
        self.env.rec_broadcast(basic_hit(self, self.current_target))
    else:
        self.target_memory -= 1
        if self.target_memory <= 0:
            self.unregister(self.combat_pulse)
            self.current_target = None
            
        
def mob_rec_violence(self, opponent):
    self.target_memory = 15
    if self.current_target:
        return
    
    self.current_target = opponent
    self.combat_pulse = self.register_p(3 * PULSES_PER_SECOND, self.mob_attack)
    
def mob_rec_damage(self, damage):
    self.health -= damage
    if self.health < 0:
        self.die()
            

def player_rec_damage(self, damage):
    pass
        
def player_rec_violence(self, opponent):
    if not self.current_target:
        self.combat_pulse = self.register_p(3 * PULSES_PER_SECOND, self.auto_attack)
    self.current_target = opponent
    
def player_auto_attack(self):
    if self.current_target:
        if self.current_target.env == self.env:
            self.env.rec_broadcast(basic_hit(self, self.current_target))
        else:
            self.current_target = None
            self.unregister(self.combat_pulse)
        

class Kill(Action):
    def __init__(self):
        Action.__init__(self, ("kill", "attack"), "violence")
        
    def execute(self, source, target, target_method, **ignore):
        source.rec_violence(target)
        target_method(source)
        return basic_hit(source, target)

