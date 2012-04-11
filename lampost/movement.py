'''
Created on Mar 1, 2012

@author: Geoffrey
'''
from action import Action, TARGET_MSG_CLASS

class Direction(Action):
    actions = set()
    ref_map = {}
    
    def __init__(self, key, desc, rev):
        Action.__init__(self, (key, desc), self, TARGET_MSG_CLASS)
        self.key = key
        self.desc = desc
        self.rev = rev
        Direction.actions.add(self)
        Direction.ref_map[key] = self
       
       
NORTH = Direction('n', 'north', 's')
SOUTH = Direction('s', 'south', 'n')
EAST = Direction('e', 'east', 'w')
WEST = Direction('w', 'west', 'e')
NE = Direction('ne', 'northeast', 'sw')
SE = Direction('se', 'southeast', 'nw')
NW = Direction('nw', 'northwest', 'se')
SW = Direction('sw', 'northeast', 'ne')
UP = Direction('u', 'up', "d")
DOWN = Direction('d', 'down', "u")


