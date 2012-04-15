'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from entity import Entity
from gameops.speciallocs import creature_limbo
from message import CLASS_DAMAGE

class Creature(Entity):
    dbo_fields = Entity.dbo_fields + ("level",)
    
    level = 1
    hp = 1
    
    def die(self):
        self.change_env(creature_limbo, "{p} expires.")
        del self
        
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_DAMAGE:
            self.hp -= lmessage.payload
            if self.hp < 0:
                self.die()
        else:
            return super(Creature, self).receive(lmessage) 
            
        
        