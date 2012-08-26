from lampost.datastore.dbo import RootDBO
from lampost.dto.display import Display, DisplayLine
from lampost.model.creature import Creature

class Player(Creature, RootDBO):
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level", "room_id", "home_room", "flavor", "user_id")
   
    imm_level = 0
    build_mode = False
      
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id.lower()
        self.target_id = self.dbo_id,
        self.name = dbo_id.capitalize()
        self.last_tell = None
        
    def on_loaded(self):
        pass
        
    def start(self):
        self.register_p(self.autosave, seconds=20)
            
    def long_desc(self, observer):
        if self.desc:
            return self.desc
        return "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."
        
    def short_desc(self, observer):
        return "{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player")
             
    def parse(self, command):
        matches, response = self.parse_command(command)
        if not matches:
            matches, response = self.parse_command(" ".join(["say", command]))
            if not matches:
                return "What?"
        if len(matches) > 1:
            return "Ambiguous command."
        if isinstance(response, basestring):
            return response
        broadcast = getattr(response, "broadcast", None)
        feedback = getattr(response, "feedback", None)
        if isinstance(feedback, basestring):
            feedback = Display(feedback)
        if broadcast:
            self.env.rec_broadcast(broadcast, broadcast.source)
            display = Display(broadcast.translate(self), broadcast.color)
            if feedback:
                feedback.merge(Display)
            else:
                feedback = display
        try:
            if response.dialog:
                self.session.dialog = response.dialog
        except AttributeError:
            pass
        return feedback  
                     
    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)
            
    def display_line(self, text, color=0x000000):
        self.session.display_line(DisplayLine(text, color))
    
    def register_channel(self, channel):
        self.register(channel, self.display_channel)
        
    def rec_broadcast(self, broadcast):
        self.display_line(broadcast.translate(self), broadcast.color)
    
    def die(self):
        pass
                               
    def detach(self):
        super(Player, self).detach()
        self.session = None

        