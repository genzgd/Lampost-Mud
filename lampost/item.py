'''
Created on Mar 11, 2012

@author: Geoff
'''
from datastore.dbo import RootDBO
from message import CLASS_SENSE_EXAMINE
from action import TARGET_ITEM

VOWELS = set(['a', 'e', 'i', 'o', 'u', 'y'])

class BaseItem(RootDBO):
    def __init__(self, name, prefixes=None):
        if not prefixes:
            self.prefixes = []
        elif isinstance(prefixes, basestring):
            self.prefixes = [prefixes]
        else:
            self.prefixes = prefixes
        self.suffix = None
        self.weight = 0
        self.name = name
        self.target_class = TARGET_ITEM
        
    def short_desc(self):
        desc = " ".join(self.prefixes + [self.name]) + '.'
        if desc[0] in VOWELS:
            desc = "An " + desc
        else:
            desc = "A " + desc
        return desc
        
    def long_desc(self):
        return self.short_desc()
        
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_SENSE_EXAMINE:
            return self.long_desc()
        
class Container(BaseItem):
    def __init__(self, name, suffix, prefixes=None):
        BaseItem.__init__(self, name, prefixes)
        self.contents = []
        self.suffix = suffix