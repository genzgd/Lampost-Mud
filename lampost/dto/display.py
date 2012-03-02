'''
Created on Feb 19, 2012

@author: Geoff
'''
from rootdto import RootDTO

class Display(RootDTO):
    def __init__(self, text=None, color=0x000000):
        self.display = RootDTO()
        self.display.lines = []
        if text is not None:
            self.append(DisplayLine(text, color))

    def merge(self, other):
        for line in other.display.lines:
            self.append(line)
 
    def append(self, line):
        self.display.lines.append(line)
        
class DisplayLine(RootDTO):
    def __init__(self, text, color=0x000000):
        self.text = text; 
        self.color = color
        
    
        
        