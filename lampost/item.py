'''
Created on Mar 11, 2012

@author: Geoff
'''
class BaseItem():
    def __init__(self):
        self.prefixes = []
        self.suffix = None
        
class Container(BaseItem):
    def __init__(self, suffix):
        BaseItem.__init__(self)
        self.contents = []
        self.suffix = suffix