'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from entity import Entity

class Creature(Entity):
    dbo_fields = Entity.dbo_fields + ("level",)
    
    level = 1
    hp = 1
    
    def die(self):
        self.leave_env("{p} expires.")
        del self
        
    def rec_damage(self, amount):
        self.hp -= amount
        if self.hp < 0:
            self.die()
        return "You zap {0}".format(self.name)    
        
        