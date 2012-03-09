'''
Created on Feb 26, 2012

@author: Geoff
'''

CLASS_OUT_OF_CHAR = 0
CLASS_COMM_GENERAL = 1
CLASS_SENSE_GLANCE = 10
CLASS_SENSE_EXAMINE = 11

CLASS_MOVEMENT = 100
CLASS_ENTER_ROOM = 101
CLASS_LEAVE_ROOM = 102

BC_ACTOR_NOTARG= 0
BC_ENV_NOTARG = 1
BC_ACTOR_WTARG = 2
BC_ENV_WTARG = 3
BC_TARG = 4
BC_ACTOR_SELFTARG = 5
BC_ENV_SELFTARG = 6


class LMessage():

    def __init__(self, source, msg_class, payload, target_id=None, broadcast=None):
        self.source = source
        self.msg_class = msg_class
        self.payload = payload
        self.target_id = target_id
        self.broadcast = broadcast        
    

#MESSAGE_CONTENT

#temporal
#  immediate
#  pulses
#
#classes:
#
#  damage
#    target:  peers
#    form
#      blunt
#      edged
#      magical
#      heat
#      cold
#      electrical
#    magnitude
#    response:  state change
#
#  communication
#    seek/respond
#    target:  env/peers/inven
#    form
#      sound
#      smell
#      sight
#      touch
#      taste
#      touch
#    target:  community
#      oob
#  payload:
#    information
#
#movement
#  target: env
#    location
#
#manipulation
#  target:  peers/inven
#    open
#    shake
#    'special'
#  response:  state change


    
