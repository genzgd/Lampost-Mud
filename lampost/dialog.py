'''
Created on Mar 8, 2012

@author: Geoff
'''
from dto.rootdto import RootDTO

DIALOG_TYPE_CONFIRM = 0
DIALOG_TYPE_OK = 1

class DialogDTO(RootDTO):
    def __init__(self, dialog):
        self.show_dialog = {}
        self.show_dialog["dialog_type"] = dialog.dialog_type
        self.show_dialog["dialog_msg"] = dialog.dialog_msg
        self.show_dialog["dialog_title"] = dialog.dialog_title
        

class Dialog():   
    def __init__(self, dialog_type, dialog_msg, dialog_title, callback=None):
        self.dialog_type = dialog_type
        self.dialog_msg = dialog_msg
        self.dialog_title = dialog_title
        self.callback = callback
        self.dialog = self
        self.feedback = DialogDTO(self)
    
     
        
        
    
        