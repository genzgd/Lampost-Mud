'''
Created on Apr 13, 2012

@author: Geoff
'''
from creature import Creature
from datastore.dbo import RootDBO
from coreobj.template import Template
from action import TARGET_MONSTER

class Mobile(Creature):
    target_class = TARGET_MONSTER
    
    def __init__(self, mobile_id):
        self.mobile_id = mobile_id

class MobileTemplate(RootDBO, Template):
    template_fields = Mobile.dbo_fields
    
    dbo_key_type = "mobile"
    dbo_fields = template_fields + ("instance_class", "world_max")
    instance_class = ".".join([Mobile.__module__, Mobile.__name__]) #@UndefinedVariable
   
    def __init__(self, dbo_id, title=None, desc=None, instance_class=None):
        self.dbo_id = dbo_id
        self.title = title
        self.desc = desc
        if instance_class:
            self.instance_class = instance_class
   
class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "mob_count", "mob_max"
    mob_count = 1
    mob_max = 1
    
    def __init__(self, mobile_id, mob_count=None, mob_max=None):
        self.mobile_id = mobile_id
        if mob_count is not None:
            self.mob_count = mob_count
        if mob_max:
            self.mob_max = mob_max
    
    
    
