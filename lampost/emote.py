'''
Created on Mar 6, 2012

@author: Geoffrey
'''
from action import Action
from message import CLASS_COMM_GENERAL, LMessage


EMOTES =  {"dance": ("You gyrate lewdly!",
                     "{p} gyrates lewdly!",
                     "You dip {t} in a tango!",
                     "{p} dips {t} in a tango!",
                     "{p} dips you in a tango!",
                     "You twist yourself in knots tangoing without a partner.",
                     "{p} dips ludicrously trying to tango with {pself}."),
           
           "blink": ("You blink rapidly in surprise.",
                     "{p} blinks rapidly in surprise",
                     "You blink rapidly at {t}.",
                     "{p} blinks rapidly at {t}.",
                     "{p} blinks rapidly at you in surprise.",
                     "You blink at yourself, but see nothing.",
                     "{p} blinks in confusion.")
           }
  

class Emotes(Action):
    def __init__(self):
        Action.__init__(self, EMOTES.keys(), CLASS_COMM_GENERAL)
             
    def create_message(self, source, verb, subject, command):
        broadcast = EMOTES[verb[0]]
        if not subject:
            broadcast = broadcast[:2]
        return LMessage(source, self.msg_class, subject, broadcast)