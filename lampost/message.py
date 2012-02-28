'''
Created on Feb 26, 2012

@author: Geoff
'''

TARGET_SELF = 0
TARGET_ENV = 1

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

class Message():
    pass

class MessageClass():
    pass


class SightMC(Message):
    pass
    
