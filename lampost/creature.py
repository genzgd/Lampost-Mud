'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from entity import Entity

class Creature(Entity):
    dbo_fields = Entity.dbo_fields + ("level",)
    
    level = 1