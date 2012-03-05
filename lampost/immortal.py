'''
Created on Mar 4, 2012

@author: Geoffrey
'''
from action import Gesture
from player import Player

IMM_LEVELS = {"none": 0, "creator": 1000, "admin": 10000, "supreme": 100000} 

class CreatePlayer(Gesture):
    def __init__(self):
        Gesture.__init__(self, "create player")
        self.imm_level = IMM_LEVELS["supreme"]
        
    def receive(self, lmessage):
        if not len(lmessage.payload):
            return "Name not specified"
        player = Player(lmessage.payload[0])
        if len(lmessage.payload) > 1:
            imm_level = IMM_LEVELS.get(lmessage.payload[1])
            if not imm_level:
                return "Invalid Immortal Level"
        else:
            imm_level = 0
        player.imm_level = imm_level
        self.save_object(player)
        