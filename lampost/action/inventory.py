'''
Created on Apr 27, 2012

@author: Geoff
'''
from lampost.action.action import Action
from lampost.dto.display import Display, DisplayLine

class GetAction(Action):
    def __init__(self):
        Action.__init__(self, ("get", "pick up"), "get")
        
    def execute(self, source, target_method, **ignored):
        return target_method(source)
        
class DropAction(Action):
    def __init__(self):
        Action.__init__(self, ("drop", "put down"), "drop")
        
    def execute(self, source, target_method, **ignored):
        return target_method(source)
        
class ShowInventory(Action):
    def __init__(self):
        Action.__init__(self, ("i", "inven"))
        
    def execute(self, source, **ignored):
        display = Display()
        if source.inven:
            for article in source.inven:
                display.append(DisplayLine(article.title))
        else:
            display.append(DisplayLine("You aren't carrying anything"))
        return display
        
class InvenContainer:
    def __init__(self):
        self.contents = []
        self.supports_drop = True
        
    def rec_entity_enters(self, source):          
        self.contents.append(source)
          
    def rec_entity_leaves(self, source):
        self.contents.remove(source)
        
    def add(self, article):
        self.contents.append(article)
        
    
       