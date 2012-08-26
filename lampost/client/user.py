from lampost.datastore.dbo import RootDBO

class User(RootDBO):
    dbo_key_type = "user"
    dbo_fields =  "email", "password", "player_ids"
    dbo_set_key = "users"
    
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id

            
        
    
    
    
    
    
