'''
Created on Mar 6, 2012

@author: Geoffrey
'''
from action import Action
from broadcast import BroadcastMap, Broadcast


EMOTES =  {"dance": BroadcastMap(s="You gyrate lewdly!",
                    e="{n} gyrates lewdly!",
                    st="You dip {N} in a tango!",
                    et="{n} dips {N} in a tango!",
                    t="{n} dips you in a tango!",
                    sf="You twist yourself in knots tangoing without a partner.",
                    ef="{n} dips ludicrously trying to tango with {F}."),
           
           "blink": BroadcastMap(s="You blink rapidly in surprise.",
                     e="{n} blinks rapidly in surprise",
                     st="You blink rapidly at {N} in surprise.",
                     et="{n} blinks rapidly at {N} in surprise.",
                     t="{n} blinks rapidly at you in surprise.",
                     sf="You blink at yourself, but see nothing.",
                     ef="{n} blinks in confusion.")
           }
  

class Emotes(Action):
    def __init__(self):
        self.rec_social = True
        Action.__init__(self, EMOTES.keys(), "social")
             
    def execute(self, source, target, verb, **ignored):
        broadcast_map = EMOTES[verb[0]]
        return Broadcast(broadcast_map, source, target)
        
