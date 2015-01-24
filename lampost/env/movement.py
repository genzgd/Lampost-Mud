from lampost.datastore.dbo import CoreDBO


class Direction(CoreDBO):
    class_id = 'direction'
    ref_map = {}
    ordered = []

    @classmethod
    def load_ref(cls, dbo_id, owner=None):
        return cls.ref_map[dbo_id] if dbo_id else None

    @classmethod
    def find_dir(cls, name):
        for key, value in cls.ref_map.items():
            if name == key or name == value.desc:
                return value

    def __init__(self, dbo_id, desc, rev_key):
        self.dbo_id = dbo_id
        self.desc = desc
        self.rev_key = rev_key
        Direction.ref_map[dbo_id] = self
        Direction.ordered.append({'dbo_id':dbo_id, 'name':desc, 'rev_key': rev_key})

    @property
    def rev_dir(self):
        return Direction.ref_map[self.rev_key]


NORTH = Direction('n', 'north', 's')
SOUTH = Direction('s', 'south', 'n')
EAST = Direction('e', 'east', 'w')
WEST = Direction('w', 'west', 'e')
UP = Direction('u', 'up', "d")
DOWN = Direction('d', 'down', "u")
NE = Direction('ne', 'northeast', 'sw')
SE = Direction('se', 'southeast', 'nw')
NW = Direction('nw', 'northwest', 'se')
SW = Direction('sw', 'southwest', 'ne')
