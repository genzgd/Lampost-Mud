'''
Created on Mar 1, 2012

@author: Geoffrey
'''
class Direction(object):
    ref_map = {}
    
    @classmethod
    def find_dir(cls, name):
        for key, value in cls.ref_map.iteritems():
            if name == key or name == value.desc:
                return value
    
    def __init__(self, key, desc, rev_key):
        self.key = key
        self.desc = desc
        self.rev_key = rev_key
        Direction.ref_map[key] = self
        
    @property
    def rev_dir(self):
        return Direction.ref_map[self.rev_key]
       
       
NORTH = Direction('n', 'north', 's')
SOUTH = Direction('s', 'south', 'n')
EAST = Direction('e', 'east', 'w')
WEST = Direction('w', 'west', 'e')
NE = Direction('ne', 'northeast', 'sw')
SE = Direction('se', 'southeast', 'nw')
NW = Direction('nw', 'northwest', 'se')
SW = Direction('sw', 'southwest', 'ne')
UP = Direction('u', 'up', "d")
DOWN = Direction('d', 'down', "u")


