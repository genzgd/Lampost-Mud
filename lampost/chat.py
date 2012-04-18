'''
Created on Apr 8, 2012

@author: Geoff
'''
from action import Action
from context import Context
from dto.display import Display
from broadcast import EnvBroadcast

class TellAction(Action):
    TELL_COLOR = 0x00a2e8
    TELL_OTHER_COLOR = 0x0033f8
           
    def __init__(self):
        Action.__init__(self, ("tell", "t"))
    
    def execute(self, source, verb, args, command):
        if not args:
            return "Tell who?"  
        return self.tell_message(source, args[0], command.partition(args[0])[2][1:])
        
    def tell_message(self, source, player_id, statement):
        session = Context.instance.sm.player_session_map.get(player_id) #@UndefinedVariable
        if not session:
            return "Cannot find " + player_id
        player = session.player
        if not statement:
            return "Say what to " + player.name + "?" 
        player.last_tell = source.dbo_id
        player.display_line(source.name + " tells you, `" + statement + "'", TellAction.TELL_COLOR)
        return Display("You tell " + player.name + ", `" + statement + "'", TellAction.TELL_OTHER_COLOR)

    
class ReplyAction(TellAction):
    def __init__(self):
        Action.__init__(self, ("reply", "r"))
        
    def execute(self, source, verb, command, **ignored):
        if not source.last_tell:
            return "You have not received a tell recently."
        ix = command.find(verb[0]) + len(verb[0]) + 1
        return self.tell_message(source, source.last_tell, command[ix:]) 

                  
class SayAction(Action):
    SAY_COLOR = 0xe15a00
    def __init__(self):
        Action.__init__(self, 'say')
    
    def execute(self, source, command, **ignored):
        space_ix = command.find(" ")
        if space_ix == -1:
            return "Say what?"
        statement = command[space_ix + 1:]
        return EnvBroadcast(source, "You say `{0}'".format(statement), "{0} says, `{1}'".format(source.name, statement), SayAction.SAY_COLOR)
        