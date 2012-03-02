'''
Created on Feb 26, 2012

@author: Geoff
'''

#  triggers
#    message_class
#
#  state change modifiers
#    level
#    skill
#    attributes
#    state
#
#  includes generator triggered by message

class Responder():
    
    def accepts(self, lmessage):
        return self.msg_class == lmessage.msg_class
    
    def get_targets(self):
        return self
    