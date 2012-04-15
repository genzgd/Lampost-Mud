'''
Created on Apr 13, 2012

@author: Geoff
'''
from item import BaseItem
from action import TARGET_ARTICLE

VOWELS = set(['a', 'e', 'i', 'o', 'u', 'y'])

class Article(BaseItem):
    target_class = TARGET_ARTICLE
    
    def short_desc(self, observer = None):
        return "{0} {1}.".format("An" if self.title[0] in VOWELS else "A", self.title)
        
    @property
    def name(self):
        return self.short_desc()
        
class Container(Article):
    def __init__(self):
        self.contents = []
        