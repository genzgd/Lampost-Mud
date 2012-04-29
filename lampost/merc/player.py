'''
Created on Apr 19, 2012

@author: Geoff
'''
from lampost.merc.combat import Kill

soul = set([Kill()])

def curr_dex(self):
    return max(3, self.perm_dex + self.mod_dex)
    
def curr_str(self):
    return max(3, self.perm_str + self.mod_str)