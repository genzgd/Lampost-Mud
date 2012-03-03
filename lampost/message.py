'''
Created on Feb 26, 2012

@author: Geoff
'''
CLASS_OUT_OF_CHAR = 0
CLASS_COMM_GENERAL = 1
CLASS_SENSE_GLANCE = 2
CLASS_SENSE_EXAMINE = 3

CLASS_MOVEMENT = 100
CLASS_ENTER_ROOM = 101
CLASS_LEAVE_ROOM = 102

class LMessage():

    def __init__(self, source, msg_class, payload, to_self=False):
        self.source = source
        self.msg_class = msg_class
        self.payload = payload
        self.to_self = to_self 
    

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


    
