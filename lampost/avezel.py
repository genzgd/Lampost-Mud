'''
Created on Feb 26, 2012

@author: Geoff
'''
from room import Room

class Avezel():
    def __init__(self):
        self.rooms = {}
        cube = Room(0, "A White Cube", "A perfect white cube, about 30 feet on a side")
        self.rooms[0] = cube