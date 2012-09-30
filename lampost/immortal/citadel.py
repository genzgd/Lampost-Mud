from lampost.action.action import  make_action
from lampost.context.resource import requires
from lampost.model.article import Article, ArticleTemplate, ArticleReset
from lampost.env.room import Room, Exit
from lampost.env.movement import UP, DOWN
from lampost.mobile.mobile import MobileTemplate, MobileReset
from lampost.comm.broadcast import SingleBroadcast
from lampost.model.item import BaseItem
from lampost.mud.area import Area
from lampost.util.lmutil import cls_name

class MusicBox(Article):
    def __init__(self, article_id):
        self.article_id = article_id
        self.rec_play = True
        self.fixed_targets = self,
        make_action(self, ["play", "wind"], "play", [self])

    def __call__(self, source, **ignored):
        return SingleBroadcast(source, "The music box plays an eerie atonal tune.")

@requires('cls_registry')
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
        blemish.config_targets()
        cube.extras.append(blemish)
        sphere.exits.append(Exit(DOWN, cube))
        self.rooms.append(cube)
        self.rooms.append(sphere)

        music_box = self.cls_registry(ArticleTemplate)("immortal_citadel:music_box")
        music_box.title ="Music Box"
        music_box.desc ="An odd, translucent music box"
        music_box.instance_class = cls_name(MusicBox)
        self.articles.append(music_box)
        music_reset = ArticleReset()
        music_reset.article_id = "immortal_citadel:music_box"
        music_reset.article_max = 3
        music_reset.article_count = 3
        sphere.article_resets.append(music_reset)

        guard = self.cls_registry(MobileTemplate)("immortal_citadel:guard")
        guard.title = "Citadel Guard"
        guard.desc = "The impassive, immaculate citadel guard"
        guard.level = 1
        self.mobiles.append(guard)
        guard_reset = MobileReset()
        guard_reset.mobile_id = "immortal_citadel:guard"
        guard_reset.mob_count = 0
        guard_reset.mob_max = 7
        cube.mobile_resets.append(guard_reset)



