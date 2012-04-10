'''
Created on Feb 26, 2012

@author: Geoff
'''
from room import Room, Exit
from item import BaseItem
from action import Action, TARGET_SELF
from message import CLASS_BROADCAST, LMessage
from area import Area

class ImmortalCitadel(Area):
    def __init__(self):
        Area.__init__(self, "immortal_citadel")
        self.name = "Immortal Citadel"
        cube = Room("immortal_citadel:0", "A White Cube", "A perfect white cube, about 30 feet on a side")
        sphere = Room("immortal_citadel:1", "A Silver Sphere", "A perfect silver sphere, with a radius of about 30 feet")
        cube.exits.append(Exit("u", sphere))
        sphere.exits.append(Exit("d", cube))
        self.rooms.append(cube)
        self.rooms.append(sphere)
        self.dbo_loaded = True
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())

        
class MusicBox(BaseItem, Action):
    def __init__(self):
        BaseItem.__init__(self, "box", "music")
        Action.__init__(self, ["play", "wind"], CLASS_BROADCAST, TARGET_SELF)
        
    def create_message(self, source, verb, target, command):
        return LMessage(source, self.msg_class, target, "The music box plays an eerie atonal tune")
        