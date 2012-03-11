'''
Created on Feb 16, 2012

@author: Geoff
'''
from dto.display import Display, DisplayLine
from dto.rootdto import RootDTO
from entity import Entity
from message import CLASS_MOVEMENT, CLASS_LEAVE_ROOM, CLASS_ENTER_ROOM,\
    BC_ACTOR_NOTARG, BC_ENV_NOTARG, BC_ACTOR_WTARG, BC_ENV_WTARG, BC_TARG,\
    BC_ACTOR_SELFTARG, BC_ENV_SELFTARG, CLASS_SENSE_EXAMINE
from creature import Creature
from dialog import DialogDTO

class Player(Creature):   
    dbo_key_type = "player"
    dbo_set_key = "players"
    dbo_fields = Creature.dbo_fields + ("imm_level",)
     
    def __init__(self, name):
        self.dbo_id = name.lower()
        self.name = name.capitalize()
        self.target_id = name.lower(),
        
    def baptise(self, soul, inven, env):
        Entity.__init__(self, soul, inven, env)
        
    def parse(self, command, retry=False):
        words = tuple(command.lower().split(" "))
        messages = list(self.match_actions(words, command))
        if not len(messages) and not retry:
            return self.parse("say " + command, True)   
        matches = list(self.match_messages(messages))
        if not matches:
            feedback = "What?" 
        elif len(matches) == 1:
            message, target = matches[0]
            feedback = target.receive(message)
            if message.broadcast:
                self.env.broadcast(self, target, message.broadcast)
                feedback = self.translate_broadcast(self, target, message.broadcast)
            elif message.dialog:
                self.session.dialog = message.dialog
                feedback = DialogDTO(message.dialog)
            if not feedback:
                return RootDTO(silent=True)
            if isinstance(feedback, RootDTO):
                return feedback
        else:
            feedback = "Ambiguous Command"
        return Display(feedback)
    
    def match_actions(self, words, command):
        for action in self.providers:
            message = action.match(self, words, command)
            if message:
                yield(message)
    
    def match_messages(self, messages):
        for message in messages:
            for target in self.targets:
                if target.accepts(message):
                    yield(message, target)
    
    def display_channel(self, message):
        if message.source != self:
            self.session.display_line(message.display_line)
            
    def display_line(self, text):
        self.session.display_line(DisplayLine(text))
    
    def register_channel(self, channel):
        self.register(channel, self.display_channel)
        
    def receive(self, lmessage):
        if lmessage.msg_class == CLASS_MOVEMENT:
            self.change_env(lmessage.payload)
        elif lmessage.msg_class == CLASS_LEAVE_ROOM:
            if lmessage.source != self:
                self.display_line(lmessage.source.name + " leaves.")
                self.update_state()
        elif lmessage.msg_class == CLASS_ENTER_ROOM:
            if lmessage.source != self:
                self.display_line(lmessage.source.name + " arrives.")
                self.update_state()
        elif lmessage.msg_class == CLASS_SENSE_EXAMINE:
            return self.short_desc() + ", a raceless, sexless, classless player."
    
    def receive_broadcast(self, source, target, broadcast):
        self.display_line(self.translate_broadcast(source, target, broadcast))
    
    def translate_broadcast(self, source, target, broadcast):
        pname = source.name
        if len(broadcast) < 3:
            if source == self:
                version = BC_ACTOR_NOTARG
            else:
                version = BC_ENV_NOTARG
            return broadcast[version].format(p=pname)

        tname = target.name 
        if source == self:
            if target == self:
                version = BC_ACTOR_SELFTARG
            else:
                version = BC_ACTOR_WTARG
        elif target == self:
            version = BC_TARG
        elif target != source:
            version = BC_ENV_WTARG
        else:
            version = BC_ENV_SELFTARG
       
        return broadcast[version].format(p=pname, t=tname, pself="themself")    
                
    def short_desc(self):
        return self.name
            
    def detach(self):
        Entity.detach(self)   
        self.session = None
        