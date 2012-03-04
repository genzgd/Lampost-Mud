'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from action import Gesture
from user import User, IMM_LEVEL_ADMIN

class CreateUser(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create user")
        self.imm_level = IMM_LEVEL_ADMIN
        
    def receive(self, lmessage):
        if not len(lmessage.payload):
            return "Name not specified"
        user = User(lmessage.payload[0])
        self.save_object(user)
        