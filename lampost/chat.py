'''
Created on Apr 8, 2012

@author: Geoff
'''
from action import Action, TARGET_ACTION
from context import Context
from message import Feedback

class TellAction(Action):
    TELL_COLOR = 0x00a2e8
           
    def __init__(self):
        Action.__init__(self, ("tell", "t"), self, TARGET_ACTION)
    
    def create_message(self, source, verb, target, command):
        if not len(target):
            return Feedback("Tell who?")
        player_id = target[0]
        session = Context.instance.sm.player_session_map.get(player_id) #@UndefinedVariable
        if not session:
            return Feedback("Cannot find " + player_id)
        player = session.player
        space_ix = command.lower().find(player_id) + len(player_id)
        if space_ix == len(command):
            return Feedback("Say what to " + player.name + "?")
        statement = command[space_ix + 1:]
        player.display_line(source.name + " tells you, `" + statement + "'", TellAction.TELL_COLOR)
        return Feedback("You tell " + player.name + ", `" + statement + "'")       