'''
Created on Feb 15, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO


class User(RootDBO):
    dbo_key_type = "user"
    dbo_fields = ("email")
    dbo_set_key = "users"
    
    def __init__(self, email):
        self.email = email
            
        
    
    
    
    
    
