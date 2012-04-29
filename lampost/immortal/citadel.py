'''
Created on Feb 26, 2012

@author: Geoff
'''
from lampost.action.action import Action
from lampost.model.article import Article, ArticleTemplate, ArticleReset
from lampost.env.room import Room, Exit
from lampost.env.movement import UP, DOWN
from lampost.mobile.mobile import MobileTemplate, MobileReset
from lampost.comm.broadcast import SingleBroadcast
from lampost.model.item import BaseItem
from lampost.mud.area import Area

class MusicBox(Article, Action):
    def __init__(self, article_id):
        self.article_id = article_id
        self.rec_play = True
        self.fixed_targets = self,
        Action.__init__(self, ["play", "wind"], "play")
        
    def execute(self, source, **ignored):
        return SingleBroadcast(source, "The music box plays an eerie atonal tune.")

class ImmortalCitadel(Area):
    def __init__(self):
        Area.__init__(self, "immortal_citadel")
        self.name = "Immortal Citadel"
        self.owner_id = "MUD"
        cube = Room("immortal_citadel:0", "A White Cube", "A perfect white cube, about 30 feet on a side.  It has a single blemish.")
        sphere = Room("immortal_citadel:1", "A Silver Sphere", "A perfect silver sphere, with a radius of about 30 feet")
        cube.exits.append(Exit(UP, sphere))
        blemish = BaseItem()
        blemish.title = "blemish"
        blemish.desc = "It's nothing, just a speck of imperfection. A bit of dust. Quit obsessing."
        blemish.aliases = ["speck", "dust"]
        blemish.config_targets();
        cube.extras.append(blemish)
        sphere.exits.append(Exit(DOWN, cube))
        self.rooms.append(cube)
        self.rooms.append(sphere)
        
        musicbox = ArticleTemplate("immortal_citadel:music_box", "Music Box", "An odd, translucent music box", MusicBox)
        self.articles.append(musicbox)
        sphere.article_resets.append(ArticleReset("immortal_citadel:music_box", 3, 3))
       
        guard = MobileTemplate("immortal_citadel:guard", "Citadel Guard", "The impassive, immaculate citadel guard")
        guard.level = 1
        self.mobiles.append(guard)
        cube.mobile_resets.append(MobileReset("immortal_citadel:guard", 0, 7))
   
        

        