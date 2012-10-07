from lampost.merc.util import scale32, range_limit
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
        source.broadcast(s="You hit {N} for " + unicode(damage) + ".", e="{n} hits {N}", t="{n} hits you!", target=target)
    else:
        target.rec_damage(0)
        source.broadcast(s="You miss {N}.", e="{n} misses {N}", t="{n} misses you!", target=target)

def calc_experience(killer, killed):
    xp = 300 - range_limit(-3, killer.level - killed.level, 6) * 50
    return xp


