'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from entity import Entity
from broadcast import Broadcast

class Creature(Entity):
    dbo_fields = Entity.dbo_fields + ("level",)
    
    level = 1
    hp = 1
    
    def die(self):
        self.exit_msg = Broadcast(s="{n} expires, permanently.", color=0xE6282D)
        self.leave_env()
        del self
        
    def rec_damage(self, amount):
        self.hp -= amount
        if self.hp < 0:
            self.die()  
        
        