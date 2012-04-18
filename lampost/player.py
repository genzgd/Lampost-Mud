'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display, DisplayLine
from entity import Entity
from creature import Creature
from datastore.dbo import RootDBO

class Player(Creature, RootDBO):   
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level", "room_id", "home_room")
   
    imm_level = 0
      
    def __init__(self, dbo_id):
        self.dbo_id = dbo_id.lower()
        self.target_id = self.dbo_id
        self.name = dbo_id.capitalize()
        self.last_tell = None
        
    def on_loaded(self):
        pass
        
    def start(self):
        self.register_p(80, self.autosave)
            
    def long_desc(self, observer):
        if self.desc:
            return self.desc
        return "An unimaginably powerful immortal." if self.imm_level else "A raceless, classless, sexless player."
        
    def short_desc(self, observer):
        return "{0}, {1}".format(self.name, self.title or "An Immortal" if self.imm_level else "A Player")
             
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        matches = list(self.match_actions(words))
        if not matches:
            if not retry:
                return self.parse("say " + command, True)   
            return "What?"
        if len(matches) > 1:
            return "Ambiguous command."
         
        action, verb, args, target, target_method = matches[0]
        response = action.execute(source=self, target=target, verb=verb, args=args,
            target_method=target_method, command=command)
        if isinstance(response, basestring):
            return response
        broadcast = getattr(response, "broadcast", None)
        feedback = getattr(response, "feedback", None)
        if broadcast:
            self.env.rec_broadcast(broadcast)
            display = Display(broadcast.translate(self), broadcast.color)
            if feedback:
                Display.merge(feedback)
            else:
                feedback = display
        try:
            if response.dialog:
                self.session.dialog = response.dialog
        except AttributeError:
            pass
        return feedback
     
    def match_actions(self, words):
        for verb_size in range(1, len(words) + 1):
            verb = words[:verb_size]
            args = words[verb_size:]    
            for action in self.actions.get(verb, []):
                msg_class = getattr(action, "msg_class", None)
                fixed_targets = getattr(action, "fixed_targets", None)
                if msg_class:           
                    for target, target_method in self.matching_targets(args, msg_class):
                        if not fixed_targets or target in fixed_targets:
                            yield action, verb, args, target, target_method
                else:
                    yield action, verb, args, action, None
                            
    def matching_targets(self, target_args, msg_class):
        for target in self.target_key_map.get(target_args, []) if target_args else [self.env]:
            target_method = target_method = getattr(target, msg_class, None)
            if target_method:
                yield target, target_method       
                     
    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)
            
    def display_line(self, text, color=0x000000):
        self.session.display_line(DisplayLine(text, color))
    
    def register_channel(self, channel):
        self.register(channel, self.display_channel)
        
    def rec_broadcast(self, broadcast):
        if self != broadcast.source:
            self.display_line(broadcast.translate(self), broadcast.color)
    
    def die(self):
        pass
                               
    def detach(self):
        Entity.detach(self)   
        self.session = None

        