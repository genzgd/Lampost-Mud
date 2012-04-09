'''
Created on Feb 19, 2012

@author: Geoff
'''
ERROR_SESSION_NOT_FOUND = "no_session"
ERROR_NOT_LOGGED_IN = "no_login"

LINK_GOOD = "good"
LINK_CANCEL = "cancel"

from dto.rootdto import RootDTO
        
class LinkGood(RootDTO):
    def __init__(self):
        self.link_status = LINK_GOOD
        
class  LinkError(RootDTO):
    def __init__(self, error_message):
        self.link_status= error_message

class LinkCancel(RootDTO):
    def __init__(self):
        self.link_cancel = LINK_CANCEL
        