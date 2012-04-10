'''
Created on Apr 8, 2012

@author: Geoffrey
'''
from action import Gesture
from immortal import IMM_LEVELS

class Dig(Gesture):
    def __init__(self):
        Gesture.__init__(self, "bdig")
        self.imm_level = IMM_LEVELS["creator"]
        
    
