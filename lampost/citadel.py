'''
Created on Feb 26, 2012

@author: Geoff
'''
from action import Action, TARGET_SELF
from area import Area
from article import Article
from message import CLASS_BROADCAST, LMessage
from room import Room, Exit
from movement import UP, DOWN
from mobile import MobileTemplate, MobileReset

class ImmortalCitadel(Area):
    def __init__(self):
        Area.__init__(self, "immortal_citadel")
        self.name = "Immortal Citadel"
        self.owner_id = "MUD"
        cube = Room("immortal_citadel:0", "A White Cube", "A perfect white cube, about 30 feet on a side")
        sphere = Room("immortal_citadel:1", "A Silver Sphere", "A perfect silver sphere, with a radius of about 30 feet")
        cube.exits.append(Exit(UP, sphere))
        sphere.exits.append(Exit(DOWN, cube))
        self.rooms.append(cube)
        self.rooms.append(sphere)
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())
        sphere.contents.append(MusicBox())
        
        self.mobiles.append(MobileTemplate("immortal_citadel:guard", "Citadel Guard", "The impassive, immaculate citadel guard"))
        cube.mobile_resets.append(MobileReset("immortal_citadel:guard", 0, 7))
   
        
class MusicBox(Article, Action):
    def __init__(self):
        self.title = "music box"
        self.desc = "An translucent music box.  It doesn't seem quite all here."
        self.config_targets()
        Action.__init__(self, ["play", "wind"], CLASS_BROADCAST, TARGET_SELF)
        
    def create_message(self, source, verb, target, command):
        return LMessage(source, self.msg_class, target, "The music box plays an eerie atonal tune.")
        