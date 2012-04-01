'''
Created on Feb 26, 2012

@author: Geoff
'''
from room import Room, Exit
from movement import UP, DOWN
from item import BaseItem
from action import Action, TARGET_ENV, TARGET_ACTION, TARGET_SELF
from message import CLASS_BROADCAST, LMessage


class Avezel():
    def __init__(self):
        self.rooms = {}
        cube = Room(0, "A White Cube", "A perfect white cube, about 30 feet on a side")
        sphere = Room(1, "A Silver Sphere", "A perfect silver sphere, with a radius of about 30 feet")
        cube.exits.append(Exit(UP, sphere))
        sphere.exits.append(Exit(DOWN, cube))
        self.rooms[0] = cube
        self.rooms[1] = sphere
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())
        
class MusicBox(BaseItem, Action):
    def __init__(self):
        BaseItem.__init__(self, "box", "music")
        Action.__init__(self, ["play", "wind"], CLASS_BROADCAST, TARGET_SELF)
        
    def create_message(self, source, verb, target, command):
        return LMessage(source, self.msg_class, target, "The music box plays an eerie atonal tune")
        