'''
Created on Apr 13, 2012

@author: Geoff
'''
from creature import Creature
from lampost.datastore.dbo import RootDBO
from lampost.coreobj.template import Template

class Mobile(Creature):    
    def __init__(self, mobile_id):
        self.mobile_id = mobile_id
               
    @property
    def name(self):
        return self.title

     
class MobileTemplate(RootDBO, Template):
    dbo_key_type = "mobile"
    instance_class = ".".join([Mobile.__module__, Mobile.__name__]) #@UndefinedVariable
    aliases= []
  
    def __init__(self, dbo_id, title=None, desc=None, instance_class=None):
        self.dbo_id = dbo_id
        self.mobile_id = dbo_id
        self.title = title
        self.desc = desc
        if instance_class:
            self.instance_class = instance_class
            
    def config_instance(self, instance):
        self.mud.init_mobile(instance)
        instance.baptise(set())

   
class MobileReset(RootDBO):
    dbo_fields = "mobile_id", "mob_count", "mob_max"
    mob_count = 1
    mob_max = 1
    
    def __init__(self, mobile_id=None, mob_count=None, mob_max=None):
        self.mobile_id = mobile_id
        if mob_count is not None:
            self.mob_count = mob_count
        if mob_max:
            self.mob_max = mob_max
    