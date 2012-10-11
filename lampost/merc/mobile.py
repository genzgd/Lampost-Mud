from random import randint
from lampost.merc.combat import basic_hit
from lampost.merc.util import nudge, scale32
from lampost.mobile.mobile import MobileTemplate, Mobile
from lampost.util.lmutil import cls_name

class MobileMerc(Mobile):

    def calc_damage(self, target):
        damage = randint(self.level / 2, self.level * 3 / 2 )
        return damage

    def rec_violence(self, opponent):
        self.target_memory = 15
        if self.current_target:
            return
        self.current_target = opponent
        self.combat_pulse = self.register_p(self.mob_attack, seconds=3)

    def rec_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.die()

    def add_exp(self):
        pass

    def mob_attack(self):
        if self.current_target.env == self.env:
            self.env.rec_broadcast(basic_hit(self, self.current_target))
        else:
            self.target_memory -= 1
            if self.target_memory <= 0:
                self.unregister(self.combat_pulse)
                self.current_target = None


class MobileTemplateMerc(MobileTemplate):
    template_fields = MobileTemplate.template_fields + ("level",)
    dbo_fields = MobileTemplate.dbo_fields + ("level",)
    instance_class = cls_name(MobileMerc)
    level = 1

    def config_instance(self, mobile):
        mobile.level = nudge(mobile.level if mobile.level else 1)
        mobile.defense = scale32(mobile.level, 100, -100)
        mobile.max_health = mobile.level * 8 + randint(mobile.level * mobile.level / 4, mobile.level * mobile.level)
        mobile.health = mobile.max_health
        return super(MobileTemplateMerc, self).config_instance(mobile)
