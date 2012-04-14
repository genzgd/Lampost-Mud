'''
Created on Apr 14, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO

class Reset(RootDBO):
    dbo_fields = ("item_id", "target_id", "params")
    
    item_id = None
    target_id = None
    params = None

        
Reset.dbo_base_class = Reset
    