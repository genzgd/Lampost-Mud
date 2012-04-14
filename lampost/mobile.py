'''
Created on Apr 13, 2012

@author: Geoff
'''
from creature import Creature
from datastore.dbo import RootDBO

class MobileTemplate(RootDBO):
    dbo_key = "mobile"
    dbo_fields = Creature.dbo_fields
    
    
    
