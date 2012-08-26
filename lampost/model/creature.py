from entity import Entity
from lampost.comm.broadcast import Broadcast

class Creature(Entity):
    dbo_fields = Entity.dbo_fields
        
    def die(self):
        self.exit_msg = Broadcast(s="{n} expires, permanently.", color=0xE6282D)
        self.leave_env()
        self.detach()
        del self          