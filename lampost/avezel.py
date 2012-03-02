'''
Created on Feb 26, 2012

@author: Geoff
'''
from room import Room, Exit
from movement import UP, DOWN


class Avezel():
    def __init__(self):
        self.rooms = {}
        cube = Room(0, "A White Cube", "A perfect white cube, about 30 feet on a side")
        sphere = Room(1, "A Silver Sphere", "A perfect silver sphere, with a radius of about 30 feet")
        cube.exits.add(Exit(UP, sphere))
        sphere.exits.add(Exit(DOWN, cube))
        self.rooms[0] = cube
        self.rooms[1] = sphere