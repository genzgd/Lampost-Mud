from lampost.datastore.dbo import RootDBO, DBOField


class Direction(RootDBO):
    ref_map = {}
    ordered = []
    key = DBOField()

    @classmethod
    def load_ref(cls, key, owner=None):
        return cls.ref_map[key]

    @classmethod
    def to_dto_repr(cls, value):
        return value.key

    @classmethod
    def to_save_repr(cls, value):
        return value.key

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
        Direction.ordered.append({'key':key, 'name':desc, 'rev_key': rev_key})

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
