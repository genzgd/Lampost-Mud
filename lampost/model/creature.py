from entity import Entity
from lampost.comm.broadcast import Broadcast

class Creature(Entity):
    dbo_fields = Entity.dbo_fields

    def die(self):
        self.exit_msg = Broadcast(s="{n} expires, permanently.", color=0xE6282D)
        for article in self.inven.copy():
            self.drop_inven(article)
        self.leave_env()
        self.detach()
        self.status = 'dead'
        del self

    def equip_article(self, article):
        pass

    @property
    def dead(self):
        return self.status == 'dead'