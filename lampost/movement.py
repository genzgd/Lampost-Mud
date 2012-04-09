'''
Created on Mar 1, 2012

@author: Geoffrey
'''
from action import Action, TARGET_MSG_CLASS

class Direction(Action):
    actions = set()
    ref_map = {}
    
    def __init__(self, key, desc):
        Action.__init__(self, (key, desc), self, TARGET_MSG_CLASS)
        self.key = key
        self.desc = desc
        Direction.actions.add(self)
        Direction.ref_map[key] = self
       
       
NORTH = Direction('n', 'north')
SOUTH = Direction('s', 'south')
EAST = Direction('e', 'east')
WEST = Direction('w', 'west')
NE = Direction('ne', 'northeast')
SE = Direction('se', 'southeast')
NW = Direction('nw', 'northwest')
NE = Direction('ne', 'northeast')
UP = Direction('u', 'up')
DOWN = Direction('d', 'down')


