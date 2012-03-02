'''
Created on Mar 1, 2012

@author: Geoffrey
'''
from action import Action

class Direction(Action):
    def __init__(self, verbs):
        Action.__init__(self, verbs, self)
        self.desc = verbs[1]
    
   
        
NORTH = Direction(('n', 'north'))
SOUTH = Direction(('s', 'south'))
EAST = Direction(('e', 'east'))
WEST = Direction(('w', 'west'))
NE = Direction(('ne', 'northeast'))
SE = Direction(('se', 'southeast'))
NW = Direction(('nw', 'northwest'))
NE = Direction(('ne', 'northeast'))
UP = Direction(('u', 'up'))
DOWN = Direction(('d', 'down'))

class Directions():
    def __init__(self):
        self.actions = set((NORTH, SOUTH, EAST, WEST, NE, SE,
                           NW, NE, UP, DOWN))
        
    def get_actions(self):
        return self.actions