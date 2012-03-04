'''
Created on Feb 15, 2012

@author: Geoff
'''
from datastore.dbo import DBODef

IMM_LEVEL_NONE = 0
IMM_LEVEL_CREATOR = 1000
IMM_LEVEL_ADMIN = 10000
IMM_LEVEL_SUPREME = 100000

class User():
    DBODef = DBODef("user", ("name", "imm_level", "level"))
    
    def __init__(self, name):
        self.name = name
        self.dbo_id = name.lower()
        self.imm_level = IMM_LEVEL_NONE
        self.level = 1
        
        
    
    
    
    
    
