'''
Created on Feb 26, 2012

@author: Geoff
'''

#trigger
#  action
#  time
#  env:
#    contents
#    state
#  
#  inputs
#    level
#    skill
#    attributes
#    
class Generator():
    def __init__(self):
        self.actions = set()
        self.children = set()
        
    def action_list(self):
        return self.actions
    
    def children(self):
        return self.children